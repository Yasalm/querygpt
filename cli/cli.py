import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.markdown import Markdown
import click
from core.agent import agent
from core.workflow import generate_insight
from config.config import init_config

console = Console()
config = init_config()


@click.command()
@click.option(
    "--query",
    prompt="Your query to the agent",
    help="The question that you would like the agent to answer.",
)
def query(query):
    final_answer = agent.run(query)
    if final_answer and hasattr(agent.tools["validate_sql_and_exceute_it"], "_final"):
        sql_result = agent.tools["validate_sql_and_exceute_it"]._final
    if final_answer and hasattr(agent.tools["sql_generator"], "_final"):
        sql_gen = agent.tools["sql_generator"]._final

    if final_answer and hasattr(
        agent.tools["generate_insghits_from_sql_result"], "_final"
    ):
        insight = agent.tools["generate_insghits_from_sql_result"]._final
    if sql_gen and not hasattr(
        agent.tools["generate_insghits_from_sql_result"], "_final"
    ):
        insight = generate_insight(
            query=query, sql_result=sql_result, config=config.llm
        )
    response = {"agent_answer": final_answer.to_string(), **sql_gen, **insight}
    if sql_result and isinstance(sql_result, list):
        if len(sql_result) >= 10:
            response["sql_result_sample"] = sql_result[:10]
        else:
            response["sql_result"] = sql_result
    markdown = Markdown(insight["insight"])
    console.print(markdown, justify="left",)
    console.print(response, justify="left")


if __name__ == "__main__":
    query()
