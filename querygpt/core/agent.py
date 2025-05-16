import yaml
import importlib
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool, TransformersModel
from querygpt.config.config import init_config
from querygpt.tools.tools import (
    TableListerTool,
    ColumnListerTool,
    GenerateSqlTool,
    SqlExecutorTool,
    ContextRetrieverTool,
    TableSchemaTool,
    TableSampleTool,
    InisghtGeneratorTool,
    FinderFinalAnswer,
    UserInputToolOverwrite,
)



config = init_config()

ENGINE = LiteLLMModel(model_id=config.llm.model, temperature=config.llm.temperature)
# model = TransformersModel(
#     model_id="Qwen/Qwen3-4B",
#     device="cuda",
#     max_new_tokens=5000,
#       )
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
]

DEFAULT_TOOLS = [
    TableListerTool(),
    ColumnListerTool(),
    GenerateSqlTool(),
    SqlExecutorTool(),
    ContextRetrieverTool(),
    TableSchemaTool(),
    TableSampleTool(),
    # InisghtGeneratorTool(),
]


def create_agent(
    task: str = "query",
    engine=ENGINE,
    planning_interval: int = 5,
    additional_authorized_imports: list = DEFULAT_AUTH_IMPORTS,
    tools: list = DEFAULT_TOOLS,
):
    if task == "query":
        tools += [InisghtGeneratorTool()]
        custom_prompt_templates = yaml.safe_load(
            importlib.resources.files("core.prompts").joinpath("query_agent.yaml").read_text()
        )
    if task == "finder":
        custom_prompt_templates = yaml.safe_load(
            importlib.resources.files("core.prompts").joinpath("finder_agent.yaml").read_text()
        )

    agent = CodeAgent(
        model=engine,
        tools=tools,
        additional_authorized_imports=additional_authorized_imports,
        planning_interval=planning_interval,
        prompt_templates=custom_prompt_templates,
    )
    return agent
