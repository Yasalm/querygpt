import time
from querygpt.core.agent import Agent
from querygpt.core.logging import get_logger

logger = get_logger(__name__)

class Orchestrator:
    """
    Orchestrator class that can be multiple agents to answer the query, defaults is a sequential of planner and query agent.
    """
    def __init__(self, agents: list[Agent], sequential: bool = True):
         """
         Args:
              agents (list[Agent]): List of agents to use.
              sequential (bool): Whether to execute the agents sequentially or in parallel. Defaults to True.
         """
         logger.info(f"Initializing Orchestrator with {len(agents) if agents else 2} agents, sequential={sequential}")
         
         if not agents:
              logger.debug("No agents provided, using default planner and query agents")
              self.agents = [Agent(task="planner", planning_interval=3), Agent(task="query", planning_interval=5)]
         else:
              logger.debug(f"Using provided agents: {[agent.agent.__class__.__name__ for agent in agents]}")
              self.agents = agents
         self.sequential = sequential
         self.history = [] # {query: query, trace_id: trace_id, agent_task: agent_task, final_answer: final_answer}
         logger.info("Orchestrator initialized successfully")
         
    def run(self, query: str):
         logger.info(f"Starting orchestrator run with query: {query[:100]}...")
         initial_plan = None
         prompt = f"""
            User: {query}, 
            planner: initial data discovery plan provided by the planner agent:
            {initial_plan}
        """.strip()
         #TODO: need to implement proper orchestration. this is still basic workflow
         if self.sequential:
              logger.info(f"Running {len(self.agents)} agents sequentially")
              for i, agent in enumerate(self.agents):
                   logger.info(f"Running agent {i+1}/{len(self.agents)}: {agent.agent.__class__.__name__}")
                   final_answer, trace_id = agent.run(query if agent.task == "planner" else prompt, use_enhanced_task=False, max_steps=25)
                   logger.debug(f"Agent {i+1} completed with trace ID: {trace_id}")
                   
                   if agent.task == "planner":
                        initial_plan = final_answer
                        logger.debug("Updated initial plan from planner agent")
                   
                   self.history.append({"query": query, "trace_id": trace_id, "agent": agent ,"final_answer": final_answer})
                   logger.debug("Added agent execution to history")
                   
                   if i < len(self.agents) - 1:  # Don't sleep after the last agent
                        logger.debug("Sleeping for 4 seconds to avoid rate limiting")
                        time.sleep(4) # to avoid rate limiting; free tier
         else:
              raise ValueError("Parallel execution is not supported yet")
         
         logger.info("Orchestrator run completed successfully")
         return final_answer
    
    def get_traces(self):
         logger.debug("Retrieving traces from orchestrator history")
         traces = {}
         for history in self.history:
              traces[history["agent"].task] = history["agent"].get_trace(history["trace_id"]).to_dict()
         logger.debug(f"Retrieved {len(traces)} traces")
         return traces

