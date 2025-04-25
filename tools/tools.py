import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from smolagents import CodeAgent, Tool, LiteLLMModel, DuckDuckGoSearchTool, FinalAnswerTool, UserInputTool
from core.sql_generator import generate_sql_from_context, validate_and_run_sql
from core.retreivers import get_context
from typing import List, Any
from config.config import init_config
from core.index import Index
from core import (
    init_database_from_config,
    init_internal_database_from_config,
    chat_completion_from_config,
)
from core.retreivers import get_context
import json

config = init_config()


source_dbs = [init_database_from_config(source.database) for source in config.sources]
source_db = source_dbs[0]  # TMP: as we only support one source for now.
internal_db = init_internal_database_from_config(config.internal_db)
index = Index(config.index)


class TableListerTool(Tool):
    name = "get_all_tables"
    description = "this tool allows you to get all tables an in a database in the format of [{'table_name': 'some_table'}]"
    inputs = {}
    output_type = "string"

    def forward(
        self,
    ):
        tables = source_db.list_all_tables()
        return json.dumps(tables.to_dict(orient="records"))


class ColumnListerTool(Tool):
    name = "get_columns"
    description = "this tool allows you to get all columns an in a database in a database either in the all columns or to a specifc table_name"
    inputs = {
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch all its column details",
            "nullable": True,
        }
    }
    output_type = "string"

    def forward(self, table_name: str = None):
        try:
            tables = source_db.list_all_columns(table_name)
            return json.dumps(tables.to_dict(orient="records"))
        except Exception as e:
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
        try:
            schema = source_db.get_table_schema(table_name)
            return json.dumps(schema.to_dict(orient="records"))
        except Exception as e:
            return json.dumps({"error": str(e)})

class FinalAnswerToolOverwrite(FinalAnswerTool):
    def forward(self, answer: Any) -> Any:
        final_answer = super().forward(answer)
        return json.dumps({
            "final_answer": final_answer,
            "version": "v.0"
        })
    
class UserInputToolOverwrite(UserInputTool):
    description = "Verify the tables, columns used with the user before running the SQL generated"
    def forward(self, question):
        user_input = input(f"{question} => ")
        return user_input
    

class TableSampleTool(Tool):
    name = "get_table_data_samples"
    description = "this tool allows you to get samples of data from a table"
    inputs = {
        "table_name": {
            "type": "string",
            "description": "table name that you want fetch sample of its data",
        }
    }
    output_type = "string"

    def forward(self, table_name: str):
        try:
            samples = source_db.get_table_sample_data(table_name)
            return json.dumps(samples.to_dict(orient="records"))
        except Exception as e:
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
        You are a data analyst. A user asked the following question:

        "{query}"

        You wrote a SQL query, and here is the result table:

        {sql_result}

        Now, analyze the result and summarize the key insights clearly and concisely. Focus on trends, patterns, anomalies, or top contributors. Use plain English suitable for a business decision-maker. If applicable, suggest one actionable takeaway.
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
        return {"insight": response.choices[0].message.content}


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
        result, error = validate_and_run_sql(sql=sql, database=source_db)
        if not error:
            result = result.to_dict(orient="records")
            self._final = result
            return json.dumps(result)
        else:
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
    description = """generate sql code from context_retiver output, context most similar related tables and column names and their bussiness and usage documentation. and then joins the retireved 
    similar table names and columns and query the database to obatin its schema, as in datatypes, constraints. etc"""
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
    }
    output_type = "string"

    def forward(self, query: str, context: List[dict]):
        respone = generate_sql_from_context(
            query=query, context=context, config=config.llm, database=source_db.engine
        )
        self._final = respone
        return respone["sql"]


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
