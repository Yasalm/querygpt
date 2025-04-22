import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool
from config.config import init_config
from tools.tools import TableListerTool, ColumnListerTool, GenerateSqlTool, SqlExecutorTool, ContextRetrieverTool, TableSchemaTool, TableSampleTool, InisghtGeneratorTool, FinalAnswerToolOverwrite

config = init_config()

model = LiteLLMModel(model_id=config.llm.model, temperature=0.7)

agent = CodeAgent(
    model=model,
    tools=[TableListerTool(), ColumnListerTool(), GenerateSqlTool(), SqlExecutorTool(), ContextRetrieverTool(), TableSchemaTool(), TableSampleTool(), InisghtGeneratorTool(), FinalAnswerToolOverwrite()],
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
)

if __name__ == "__main__":
    query = "Which actors who have appeared in movies together more than others?"
    final_answer = agent.run(query)

    sql_result = agent.tools['validate_sql_and_exceute_it']._final 
    sql_gen = agent.tools["sql_generator"]._final

    print({**sql_gen,
        "sql_result": sql_result
    })




