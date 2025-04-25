import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool
from config.config import init_config
from tools.tools import (
    TableListerTool,
    ColumnListerTool,
    GenerateSqlTool,
    SqlExecutorTool,
    ContextRetrieverTool,
    TableSchemaTool,
    TableSampleTool,
    InisghtGeneratorTool,
    FinalAnswerToolOverwrite,
    UserInputToolOverwrite,
)

config = init_config()

model = LiteLLMModel(model_id=config.llm.model, temperature=0.7)

agent = CodeAgent(
    model=model,
    tools=[
        TableListerTool(),
        ColumnListerTool(),
        GenerateSqlTool(),
        SqlExecutorTool(),
        ContextRetrieverTool(),
        TableSchemaTool(),
        TableSampleTool(),
        InisghtGeneratorTool(),
    ],
    additional_authorized_imports=[
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
    ],
    planning_interval=5,
    max_steps=35
)

if __name__ == "__main__":
    query = "What is the average film length for movies in the Comedy genre?"
    for step_result in agent.run(query, stream=True):
        print(type(step_result), dir(step_result))

    sql_result = agent.tools["validate_sql_and_exceute_it"]._final
    sql_gen = agent.tools["sql_generator"]._final

    print({**sql_gen, "sql_result": sql_result})
