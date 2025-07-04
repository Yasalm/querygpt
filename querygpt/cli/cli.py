import click
from rich.console import Console
from rich.markdown import Markdown
from querygpt.core.agent import create_agent
from querygpt.core.workflow import generate_insight
from querygpt.config.config import init_config
from querygpt.core import init_sources_documentation_from_config
from querygpt.core.logging import get_logger
from rich.syntax import Syntax
import json

logger = get_logger(__name__)


console = Console()
config = init_config()

#TODO: ADD OPTION to select source names or all ( config has name for each source)
@click.group()
def main():
    """cli entry point for querygpt."""
    pass

@main.command()
def generate():
    """generate the sources documentation and other necessary setup."""
    logger.info("Starting documentation generation from database sources")
    console.print("Generating documentation from database sources...", style="bold green")
    try:
        init_sources_documentation_from_config(config=config)
        logger.info("Documentation generation completed successfully")
        console.print("Generating complete. You can now use `query` to interact with the agent.", style="bold green")
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        console.print(f"Generating failed. encountered the following error {str(e)}.", style="bold red")

@main.command()
@click.argument('finder')
def finder(finder):
    """Ask the agent to answer the query."""
    logger.info(f"Starting finder query: {finder[:100]}...")
    try:
        agent = create_agent(task="finder")
        logger.debug("Finder agent created successfully")
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
        logger.info("Finder query completed successfully")

    except Exception as e:
        logger.error(f"Finder query failed: {e}")
        console.print(f"Error processing query: {str(e)}", style="bold red")

@main.command()
@click.argument('query')
def query(query):
    """Ask the agent to answer the query."""
    logger.info(f"Starting query: {query[:100]}...")
    try:
        agent = create_agent(task="query")
        logger.debug("Query agent created successfully")
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
        logger.info("Query completed successfully")

    except Exception as e:
        logger.error(f"Query failed: {e}")
        console.print(f"Error processing query: {str(e)}", style="bold red")


if __name__ == "__main__":
    main()
