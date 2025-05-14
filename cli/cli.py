import sys
import os
import click
from rich.console import Console
from rich.markdown import Markdown
from core.agent import create_agent
from core.workflow import generate_insight
from config.config import init_config
from core import init_sources_documentation_from_config
from rich.syntax import Syntax
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()
config = init_config()

#TODO: ADD OPTION to select source names or all ( config has name for each source)
@click.group()
def cli():
    """Main entry point for querygpt."""
    pass

@cli.command()
def generate():
    """generate the sources documentation and other necessary setup."""
    console.print("Generating documentation from database sources...", style="bold green")
    try:
        init_sources_documentation_from_config(config=config)
        console.print("Generating complete. You can now use `query` to interact with the agent.", style="bold green")
    except Exception as e:
        console.print(f"Generating failed. encountered the following error {str(e)}.", style="bold red")

@cli.command()
@click.argument('finder')
def finder(finder):
    """Ask the agent to answer the query."""
    try:
        agent = create_agent(task="finder")
        final_answer = agent.run(finder, max_steps=25)
        sql_result = None
        sql_gen = None

        if final_answer and hasattr(agent.tools["validate_sql_and_exceute_it"], "_final"):
            sql_result = agent.tools["validate_sql_and_exceute_it"]._final

        if final_answer and hasattr(agent.tools["sql_generator"], "_final"):
            sql_gen = agent.tools["sql_generator"]._final

        final_answer = final_answer.to_string() if hasattr(final_answer, "to_string") else final_answer
        
        response = {"agent": final_answer, **(sql_gen or {})}

        if sql_result and isinstance(sql_result, list):
            if len(sql_result) >= 10:
                response["sql_result_sample"] = sql_result[:5]
            else:
                response["sql_result"] = sql_result

        syntax = Syntax(json.dumps(response, indent=4), "json", theme="monokai", line_numbers=True)
        console.print(syntax,)

    except Exception as e:
        console.print(f"Error processing query: {str(e)}", style="bold red")

@cli.command()
@click.argument('query')
def query(query):
    """Ask the agent to answer the query."""
    try:
        agent = create_agent(task="query")
        final_answer = agent.run(query)
        sql_result = None
        sql_gen = None
        insight = None

        if final_answer and hasattr(agent.tools["validate_sql_and_exceute_it"], "_final"):
            sql_result = agent.tools["validate_sql_and_exceute_it"]._final

        if final_answer and hasattr(agent.tools["sql_generator"], "_final"):
            sql_gen = agent.tools["sql_generator"]._final

        if final_answer and hasattr(agent.tools["generate_insghits_from_sql_result"], "_final"):
            insight = agent.tools["generate_insghits_from_sql_result"]._final

        if sql_gen and not insight:
            insight = generate_insight(
                query=query, sql_result=sql_result, config=config.llm
            )

        final_answer = final_answer.to_string() if hasattr(final_answer, "to_string") else final_answer
        
        response = {"agent_answer": final_answer, **(sql_gen or {}), **(insight or {})}

        if sql_result and isinstance(sql_result, list):
            if len(sql_result) >= 10:
                response["sql_result_sample"] = sql_result[:2]
            else:
                response["sql_result"] = sql_result

        if insight and "insight" in insight:
            markdown = Markdown(insight["insight"])
            console.print(markdown, justify="left")
        if isinstance(final_answer, str):
            markdown = Markdown(f'\n\nAgent Final Answer: {final_answer}')
            console.print(markdown, justify="left")
        syntax = Syntax(json.dumps(response, indent=5), "json", theme="monokai", line_numbers=True)
        console.print(syntax, justify="left")

    except Exception as e:
        console.print(f"Error processing query: {str(e)}", style="bold red")


if __name__ == "__main__":
    cli()
