import yaml
import importlib
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool, TransformersModel
from querygpt.config.config import init_config, Config
from querygpt.tools.tools import (
    TableListerTool,
    ColumnListerTool,
    GenerateSqlTool,
    SqlExecutorTool,
    ContextRetrieverTool,
    TableSchemaTool,
    TableSampleTool,
    InisghtGeneratorTool,
    TableReferencesTool
)
from querygpt.core.trace import Trace, TraceStep, ToolCall
from querygpt.core.query_enhacner import enhance_user_question
from querygpt.core._database import InternalDatabase
from querygpt.core.logging import get_logger
import json
import time

logger = get_logger(__name__)

config = init_config()

internal_db = InternalDatabase(config.internal_db)


ENGINE = LiteLLMModel(
    model_id=config.llm.model, 
    temperature=config.llm.temperature,
)

DEFULAT_AUTH_IMPORTS = [
    "unicodedata",
    "itertools",
    "stat",
    "re",
    "datetime",
    "statistics",
    "collections",
    "math",
    "time",
    "queue",
    "json",
    "pandas"
]

DEFAULT_TOOLS = [
    TableListerTool(),
    ColumnListerTool(),
    GenerateSqlTool(),
    SqlExecutorTool(),
    ContextRetrieverTool(),
    TableSchemaTool(),
    TableSampleTool(),
    TableReferencesTool()
]

PLANNER_TOOLS = [
    TableListerTool(),
    ColumnListerTool(),
    TableSchemaTool(),
    TableSampleTool(),
    TableReferencesTool(),
    ContextRetrieverTool()
]

def create_agent(
    task: str = "query",
    engine=ENGINE,
    planning_interval: int = 1,
    additional_authorized_imports: list = DEFULAT_AUTH_IMPORTS,
    tools: list = DEFAULT_TOOLS,
):
    if task == "query":
        tools = DEFAULT_TOOLS + [InisghtGeneratorTool()]
        custom_prompt_templates = yaml.safe_load(
            importlib.resources.files("querygpt.core.prompts").joinpath("query_agent.yaml").read_text()
        )
    elif task == "planner":
        custom_prompt_templates = yaml.safe_load(
            importlib.resources.files("querygpt.core.prompts").joinpath("query_agent_plan_first.yaml").read_text()
        )
    else:
        raise ValueError(f"Invalid task: {task}, available tasks: query, planner")

    agent = CodeAgent(
        model=engine,
        tools=tools if task == "query" else PLANNER_TOOLS,
        additional_authorized_imports=additional_authorized_imports,
        planning_interval=planning_interval,
        prompt_templates=custom_prompt_templates,
    )
    return agent


class Agent:
    """Agent class that can be used to run a task with a trace of its execution and save the trace into the database.

    Args:
        task (str): Type of agent, can be "query" or "planner". Defaults to "query".
        engine: LLM model to use. Defaults to LiteLLMModel(openai).
        planning_interval (int): Interval to plan. Defaults to 5.
        additional_authorized_imports (list): Additional authorized imports. Defaults to:
            - unicodedata
            - itertools
            - stat
            - re
            - datetime
            - statistics
            - collections
            - math
            - time
            - queue
            - json
        tools (list): Tools to use. Defaults to:
            - tools.TableListerTool
            - tools.ColumnListerTool
            - tools.GenerateSqlTool
            - tools.SqlExecutorTool
            - tools.ContextRetrieverTool
            - tools.TableSchemaTool
            - tools.TableSampleTool
            -  ++ tools.InisghtGeneratorTool if the task if query
    """
    def __init__(self, task: str = "query", engine=ENGINE, planning_interval: int = 5, additional_authorized_imports: list = DEFULAT_AUTH_IMPORTS, tools: list = DEFAULT_TOOLS):
        self.agent = create_agent(task=task, engine=engine, planning_interval=planning_interval, additional_authorized_imports=additional_authorized_imports, tools=tools)
        self.task = task
        self.traces = {}
        logger.debug(f"Agent initialized successfully with {len(tools)} tools")
    
    def run(self, query: str, max_steps: int = 50, use_enhanced_task: bool = True) -> tuple[str, str]:
        """Run the agent with tracing enabled to record the execution steps.

        Args:s
            query (str): The user's query or task to execute
            max_steps (int, optional): Maximum number of steps to execute. Defaults to 50.
            use_enhanced_task (bool, optional): Whether to enhance the user's query before execution. Defaults to True.

        Returns:
            Trace: A trace object containing the complete execution history including:
                - All planning steps
                - All action steps with tool calls
                - Final answer
                - Timing information
                - Any errors that occurred
        """
        logger.info(f"Starting agent run with query: {query[:100]}...")
        logger.debug(f"Run parameters: max_steps={max_steps}, use_enhanced_task={use_enhanced_task}")
        
        trace = Trace(task=query)
        if use_enhanced_task:
            logger.debug("Enhancing user question")
            enhanced_task = enhance_user_question(query, config.llm)
            trace.enhanced_task = enhanced_task.enhanced_question
            logger.debug(f"Enhanced question: {enhanced_task.enhanced_question[:100]}...")

        for step_num, step in enumerate(self.agent.run(enhanced_task.enhanced_question if use_enhanced_task else query, stream=True, max_steps=max_steps)):
            logger.debug(f"Processing step {step_num + 1}: {step.__class__.__name__}")
            
            if step.__class__.__name__ == 'FinalAnswerStep':
                logger.info("Agent completed successfully with final answer")
                tracestep = TraceStep(
                    step_type=step.__class__.__name__,
                    model_output=json.dumps(step.final_answer),
                    trace_id=trace.id,
                )
                trace.add_step(tracestep)
                trace.finish(json.dumps(step.final_answer))

            elif step.__class__.__name__ == 'PlanningStep':
                logger.debug(f"Planning step: {step.plan[:100] if step.plan else 'No plan'}...")
                tracestep = TraceStep(
                    step_type=step.__class__.__name__,
                    trace_id=trace.id,
                    plan=step.plan,
                )
                messages = [{i['role'].value: i['content'] for i in step.model_input_messages}]
                tracestep.model_input = json.dumps(messages)
                trace.add_step(tracestep)

            elif step.__class__.__name__ == 'ActionStep':
                logger.debug(f"Action step duration: {step.duration:.2f}s")
                if step.error:
                    logger.warning(f"Action step error: {step.error.message}")
                
                tracestep = TraceStep(
                    step_type=step.__class__.__name__,
                    trace_id=trace.id,
                    start_time=step.start_time,
                    end_time=step.end_time,
                    duration_seconds=step.duration,
                    model_output=step.model_output,
                    observations=step.observations,
                    action_output=step.action_output,
                    error=step.error.message if step.error else None,
                )
                
                tool_calls = []
                if step.tool_calls is not None:
                    logger.debug(f"Processing {len(step.tool_calls)} tool calls")
                    for tool_call in step.tool_calls:
                        logger.debug(f"Tool call: {tool_call.name}")
                        tool_calls.append(json.dumps(tool_call.dict()))
                    tracestep.tool_calls_json = tool_calls
                
                    tools = [
                        ToolCall(
                            tracestep_id=tracestep.id,
                            id=tool_call.id,
                            name=tool_call.name,
                            arguments=tool_call.arguments
                        )
                        for tool_call in step.tool_calls
                    ]
                    tracestep.tool_calls = tools
                else:
                    tracestep.tool_calls = []
                
                messages = [{i['role'].value: i['content'] for i in step.model_input_messages}]
                tracestep.model_input = json.dumps(messages)
                trace.add_step(tracestep)
        
        logger.info(f"Saving trace to database with ID: {trace.id}")
        try:
            _ = internal_db.save_trace(trace)
            logger.debug("Trace saved successfully")
        except Exception as e:
            logger.error(f"Failed to save trace: {e}")
            raise
        
        self.traces[trace.id] = trace
        logger.info(f"Agent run completed. Total steps: {len(trace.steps)}, Duration: {trace.duration_seconds:.2f}s")
        return trace.final_answer, trace.id
    def get_trace(self, trace_id: str) -> Trace:
        return self.traces[trace_id]
    