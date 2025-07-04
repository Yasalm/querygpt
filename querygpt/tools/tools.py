from pydantic import BaseModel
from smolagents import (
    CodeAgent,
    Tool,
    LiteLLMModel,
    DuckDuckGoSearchTool,
    FinalAnswerTool,
    UserInputTool,
)
from querygpt.core.sql_generator import generate_sql_from_context, validate_and_run_sql
from querygpt.core.retreivers import get_context
from typing import List, Any, Dict
from querygpt.config.config import init_config
from querygpt.core.index import get_index
from querygpt.core import (
    init_database_from_config,
    init_internal_database_from_config,
    chat_completion_from_config,
)
from querygpt.core.logging import get_logger
import json

logger = get_logger(__name__)

config = init_config()


source_dbs = [init_database_from_config(source.database) for source in config.sources]
source_db = source_dbs[0]  # TMP: as we only support one source for now.
internal_db = init_internal_database_from_config(config.internal_db)
index = get_index(config.index)


class TableListerTool(Tool):
    name = "get_all_tables"
    description = "this tool allows you to get all tables an in a database in the format of [{'table_name': 'some_table'}]"
    inputs = {}
    output_type = "string"

    def forward(
        self,
    ):
        logger.debug("Getting all tables from database")
        tables = source_db.list_all_tables()
        result = json.dumps(tables.to_dict(orient="records"))
        logger.debug(f"Retrieved {len(tables)} tables")
        return result


class TableReferencesTool(Tool):
    name = "get_table_references"
    description = """this tool allows you to get all references to a table in a database in the format of 
        - relation_direction: Indicates FK direction (i.e: FROM actor → or TO actor ←).
        - constraint_name: Name of the foreign key constraint.
        - source_table: Table where the FK is defined.
        - source_column: Column in the source table that holds the FK.
        - referenced_table: Table being referenced.
        - referenced_column: Column in the referenced table (usually PK).
        - explanation: Human-readable summary of the FK relationship."""
    inputs = {
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch all its references",
        }
    }
    output_type = "string"

    def forward(self, table_name: str):
        logger.debug(f"Getting table references for: {table_name}")
        references = source_db.get_table_references(table_name)
        result = json.dumps(references.to_dict(orient="records"))
        logger.debug(f"Retrieved {len(references)} references for table {table_name}")
        return result


class ColumnListerTool(Tool):
    name = "get_columns"
    description = "this tool allows you to get all columns a table in a database either in the all columns or to a specific table_name, table_schema"
    inputs = {
        "table_schema": {
            "type": "string",
            "description": "schema or database of where the table is stored",
            "nullable": True,
        },
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch all its column details",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(self, table_schema: str = None, table_name: str = None):
        logger.debug(f"Getting columns for schema: {table_schema}, table: {table_name}")
        try:
            tables = source_db.list_all_columns(table_schema, table_name)
            result = json.dumps(tables.to_dict(orient="records"))
            logger.debug(f"Retrieved {len(tables)} columns")
            return result
        except Exception as e:
            logger.error(f"Error getting columns: {e}")
            return json.dumps({"error": str(e)})


class TableSchemaTool(Tool):
    name = "get_table_schema"
    description = "this tool allows you to get the table schema in a database"
    inputs = {
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch all its column details",
        }
    }
    output_type = "string"

    def forward(self, table_name: str):
        logger.debug(f"Getting table schema for: {table_name}")
        try:
            schema = source_db.get_table_schema(table_name)
            result = json.dumps(schema.to_dict(orient="records"))
            logger.debug(f"Retrieved schema for table {table_name}")
            return result
        except Exception as e:
            logger.error(f"Error getting table schema for {table_name}: {e}")
            return json.dumps({"error": str(e)})


class FinderFinalAnswer(FinalAnswerTool):
    description = "Provides a final answer to the given problem."
    inputs = {
        "sql": {"type": "string", "description": "SQL that answer the given problem"},
        "tables": {
            "type": "string",
            "description": "SQL tables in databases needed to answer the given problem",
        },
        "columns": {
            "type": "string",
            "description": "SQL columns in databases needed to answer the given problem",
        },
        "operations": {
            "type": "string",
            "description": "Any SQL operation that is needed to be done on tables and columns to answer the given problem",
        },
    }

    def forward(self, sql: str, tables, columns, operations) -> Any:
        return json.dumps(
            {"sql": sql, "tables": tables, "columns": columns, "operations": operations}
        )


class UserInputToolOverwrite(UserInputTool):
    description = (
        "Verify the tables, columns used with the user before running the SQL generated"
    )

    def forward(self, question):
        user_input = input(f"{question} => ")
        return user_input


class TableSampleTool(Tool):
    name = "get_table_data_samples"
    description = "this tool allows you to get samples of data from a table"
    inputs = {
        "table_schema": {
            "type": "string",
            "description": "schema or database of where the table is stored",
        },
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch sample of its data",
        },
    }
    output_type = "string"

    def forward(self, table_schema: str, table_name: str):
        logger.debug(f"Getting sample data for table: {table_schema}.{table_name}")
        try:
            samples = source_db.get_table_sample_data(table_schema, table_name)
            # quick-fix: to handle timestamp be json serilazble :(
            for col in samples.select_dtypes(include=["datetime"]).columns:
                samples[col] = samples[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
            result = json.dumps(samples.to_dict(orient="records"))
            logger.debug(f"Retrieved {len(samples)} sample rows for table {table_schema}.{table_name}")
            return result
        except Exception as e:
            logger.error(f"Error getting sample data for {table_schema}.{table_name}: {e}")
            return json.dumps({"error": str(e)})


class InisghtGeneratorTool(Tool):
    name = "generate_insghits_from_sql_result"
    description = (
        "this tool allows you to generate humen readable insights from the query result"
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "a natural language question asked by user",
        },
        "sql_result": {
            "type": "string",
            "description": "containts the results of running 'validate_sql_and_exceute_it' which is a list of dicts containing SQL query results",
        },
    }
    output_type = "string"

    def forward(self, query: str, sql_result: str):
        try:
            insights = self._generate_insight(query=query, sql_result=sql_result)
            self._final = insights
            return json.dumps(insights)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _generate_insight(self, query: str, sql_result):
        prompt = f"""
        You are a senior data analyst with expertise in business intelligence and data storytelling. A user asked the following question:

        "{query}"

        You wrote a SQL query, and here is the result table:

        {sql_result}

        Based on the nature of the query and the results, provide an appropriate analysis in markdown format. Not all queries require deep analysis - some may need just a simple answer or summary.

        For straightforward queries (e.g., looking up specific values, counting records, or simple aggregations), provide a concise response with appropriate headings that reflect the query's purpose.

        For queries that benefit from deeper analysis (e.g., trends, patterns, comparisons, or business insights), structure your response with relevant headings that emerge from the data analysis.

        Guidelines for your response:
        1. Use markdown formatting for structure and readability
        2. Create headings that reflect the actual content and insights
        3. Include only sections that are relevant to the query and data
        4. For simple queries, focus on direct answers and essential context
        5. For complex analysis, include:
           - A clear summary of findings
           - Relevant data patterns and insights
           - Business implications where applicable
           - Actionable recommendations if valuable
           - Important limitations or considerations

        Remember:
        - Structure should emerge from the data, not follow a rigid template
        - Focus on clarity and relevance
        - Use appropriate markdown formatting (headings, lists, tables, etc.)
        - Keep the response as concise as possible while being complete
        - Not every query needs a full analysis - match the depth to the query's needs
        - Provide direct answers without introductory phrases like "I'll analyze" or "Let me help"
        - Start with the most important information immediately
        """
        messages = [
            {
                "role": "system",
                "content": f"You are a data analyst expert.",
            },
            {"role": "user", "content": prompt},
        ]

        response = chat_completion_from_config(
            messages=messages,
            config=config.llm,
        )
        return response.choices[0].message.content


class SqlExecutorTool(Tool):
    name = "validate_sql_and_exceute_it"
    description = "validate the provided sql on database to make sure it is runnable. if it is runnable it will return the result of the sql query"
    inputs = {
        "sql": {
            "type": "string",
            "description": "SQL code to be validated and run on sql database",
        }
    }
    output_type = "string"

    def forward(self, sql: str):
        logger.debug(f"Executing SQL: {sql[:100]}...")
        result, error = validate_and_run_sql(sql=sql, database=source_db)
        if not error:
            for col in result.select_dtypes(include=["datetime"]).columns:
                result[col] = result[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
            result = result.to_dict(orient="records")
            self._final = result
            logger.debug(f"SQL executed successfully, returned {len(result)} rows")
            return json.dumps(result)
        else:
            logger.error(f"SQL execution failed: {error}")
            return json.dumps({"error": error})


class ContextRetrieverTool(Tool):
    name = "context_retiver"
    description = """this tool provides you similarity search on provided natural langague (question) against vector database to obtain most similar related tables and column names and their bussiness and usage documentation. and then joins the retireved 
    similar table names and columns and query the database to obatin its schema, as in datatypes, constraints. etc."""
    inputs = {
        "query": {
            "type": "string",
            "description": "a natural question to fetch most similar tables and columns with",
        }
    }
    output_type = "string"

    def forward(self, query: str):
        return json.dumps(
            get_context(
                query=query, index=index, internal_db=internal_db, source=source_db
            )
        )


class GenerateSqlTool(Tool):
    name = "sql_generator"
    description = """Generates SQL code based on the context provided by the context_retriever tool. 
    query: is the natural language question that would be translated into a SQL code.
    context: is the context provided by the context_retriever tool.
    instructions: is your instructions for enhancing the SQL query.
    previous_sql: is the previous SQL query that needs to be modified if applicable.
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "a natural language question that would be translated into a SQL code.",
        },
        "context": {
            "type": "array",
            "description": "Array of table and column metadata",
            "items": {
                "type": "object",
                "properties": {
                    "table_id": {"type": "integer"},
                    "table_name": {"type": "string"},
                    "table_bussines_summary": {"type": "string"},
                    "table_possible_usages": {"type": "string"},
                    "id": {"type": "integer"},
                    "column_name": {"type": "string"},
                    "column_details_summary": {"type": "string"},
                    "bussines_summary": {"type": "string"},
                    "possible_usages": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "table_schema": {"type": "string"},
                    "data_type": {"type": "string"},
                    "is_nullable": {"type": "string"},
                    "constraint_type": {"type": "string"},
                    "foreign_key_reference": {"type": ["string", "null"]},
                },
            },
        },
        "instructions": {
            "type": "string",
            "description": "Instructions to enhance previous sql query after you ran it and got the result or there is an error. if you have no previous sql query, this is your first try",
            "nullable": True,
        },
        "previous_sql": {
            "type": "string",
            "description": "Previous sql query if provided, otherwise this is your first try or it is irrelevant. if you have no previous sql query, this is your first try",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(
        self,
        query: str,
        context: List[dict],
        instructions: str | None = None,
        previous_sql: str | None = None,
    ):
        respone = generate_sql_from_context(
            query=query,
            context=context,
            config=config.llm,
            database=source_db.engine,
            instructions=instructions,
            previous_sql=previous_sql,
        )
        self._final = respone
        return respone["sql"]


class VisualizationGenerator(Tool):
    name = "generate_visualization"
    description = "Generate an HTML visualization (chart/graph) from SQL query results for display in the frontend"
    inputs = {
        "query": {
            "type": "string",
            "description": "The original natural language query asked by the user",
        },
        "sql_result": {
            "type": "string",
            "description": "The SQL query results as a JSON string (list of dictionaries)",
        },
        "visualization_type": {
            "type": "string",
            "description": "Optional visualization type suggestion (bar, line, pie, scatter, etc.)",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(self, query: str, sql_result: str, visualization_type: str = None):
        try:
            # Parse the SQL result
            if isinstance(sql_result, str):
                data = json.loads(sql_result)
            else:
                data = sql_result

            # Generate visualization
            visualization_html = self._generate_visualization(
                query=query, data=data, visualization_type=visualization_type
            )

            self._final = {"visualization_html": visualization_html}
            return json.dumps({"visualization_html": visualization_html})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _generate_visualization(
        self, query: str, data: List[Dict[str, Any]], visualization_type: str = None
    ):
        """Generate an HTML visualization based on the data"""

        # Create a prompt for the LLM to generate visualization code

        prompt = f"""
    You are a senior data visualization expert. A user asked the following question:

    "{query}"

    Here are the SQL query results (first 10 rows shown):

    {json.dumps(data[:10], indent=2)} {'...' if len(data) > 10 else ''}

    Your task is to create a **professional, BI-grade HTML visualization** using **Chart.js (https://www.chartjs.org/)** that effectively communicates this data.

    Requirements:
    1. Choose the most appropriate chart type to clearly communicate insights (unless specified: {visualization_type if visualization_type else 'you decide'}).
    2. Use **clean, minimal, executive-style formatting**—as seen in professional BI tools like Power BI, Tableau, or Looker.
    3. Color scheme must be professional and sophisticated:
       - Use a darker, muted color palette with rich tones instead of bright high-contrast colors
       - Prefer deep blues, dark teals, rich purples, charcoal grays, and subtle earth tones
       - Avoid primary colors (red, bright blue, yellow) and neon/flashy colors
       - For multiple data series, use colors from the same tonal family that work harmoniously
       - Ensure sufficient contrast for readability while maintaining a cohesive look
    4. Chart dimensions and responsiveness:
       - Set the chart canvas to a width of 800px and height of 500px for proper visibility
       - Include responsive: true in Chart.js options to handle different screen sizes
       - Use appropriate margins and padding (at least 20px) around the chart
       - Ensure the chart container is centered on the page
       - Include appropriate aspect ratio to prevent distortion
    5. Include:
       - A clear **title** and **legend**
       - Axis labels (if applicable)
       - Data tooltips for interactivity
       - Gridlines only if they enhance clarity
       - Appropriate number formatting (e.g., commas for thousands, currency if relevant)
    6. The HTML must be:
       - A **complete, self-contained page**
       - Load Chart.js from a **CDN**
       - Ready to render directly in a modern browser
       - Free of external dependencies

    Your output must be **only the valid HTML code**, with no explanations or Markdown formatting.
        """

        messages = [
            {
                "role": "system",
                "content": "You are a data visualization expert specializing in Chart.js. Generate only valid, complete HTML code with no explanations.",
            },
            {"role": "user", "content": prompt},
        ]

        response = chat_completion_from_config(messages=messages, config=config.llm)

        visualization_code = response.choices[0].message.content

        # Extract just the HTML if there's any markdown or explanation text
        if "```html" in visualization_code:
            visualization_code = (
                visualization_code.split("```html")[1].split("```")[0].strip()
            )
        elif "```" in visualization_code:
            visualization_code = (
                visualization_code.split("```")[1].split("```")[0].strip()
            )

        return visualization_code


# agent = CodeAgent(
#     model=model,
#     tools=[DatabaseTool(), ContextRetriever(), GenerateSqlTool(), SqlRunner()],
#     additional_authorized_imports=['unicodedata', 'itertools', 'stat', 're',
# 'datetime', 'statistics', 'collections', 'math', 'time', 'queue', 'json'], planning_interval=5
# )

# if __name__ == "__main__":
#     query = "Which actors have appeared in more than five films?"
#     response = agent.run(query)
#     print(response)
