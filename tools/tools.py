import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from smolagents import CodeAgent, Tool, LiteLLMModel, DuckDuckGoSearchTool
from core.sql_generator import generate_sql_from_context, validate_and_run_sql
from core.retreivers import get_context
from typing import List
from config.config import init_config
from core.index import Index
from core import (
    init_database_from_config,
    init_internal_database_from_config,
)
from core.retreivers import get_context
import json

config = init_config()


source_dbs = [init_database_from_config(source.database) for source in config.sources]
source_db = source_dbs[0]  # TMP: as we only support one source for now.
internal_db = init_internal_database_from_config(config.internal_db)
index = Index(config.index)

model = LiteLLMModel(
    model_id="gemini/gemini-1.5-flash",  
    temperature=0.7
)


# class Thinker(Tool):
#     name = "thinker"
#     description = "Thinks deeply about a topic using the LLM."
#     inputs = {"question": {"type": "string", "description": "the question to be thinked about"}}
#     output_type = "string"

#     def forward(self, question: str) -> str:
#         return f"{question}...Thinkinig" * 15
class SqlRunner(Tool):
    name = "sql_validator_and_runner"
    description = "validate and run the generated sql code"
    inputs = {
        "sql": {
            "type": "string",
            "description": "SQL code to be validated and run on sql database"
        }
    }
    output_type = "string"
    def forward(self, sql: str):
        result, error = validate_and_run_sql(sql=sql, database=source_db)
        if not error:
            return json.dumps(result.to_dict(orient="records"))
        else:
            return json.dumps(
                {"error": error}
            )
    
class ContextRetriever(Tool):
    name = "context_retiver"
    description = "getting context (table and columns documentation and schema) from a natural language query"
    inputs = {
        "query": {
            "type": "string",
            "description": "the natural language query asked by user"
        }
    }
    output_type = "string"
    def forward(self, query: str):
        return json.dumps(get_context(query=query, index=index, internal_db=internal_db, source= source_db))

class GenerateSqlTool(Tool):
    name = "sql_generator"
    description = """generate sql code from context, context is schema of tables, columns, and documentations, documentations is a data 
    dictionary covering the usage of these tables and columns"""
    inputs = {
        "query": {
            "type": "string",
            "description": "the natural language query asked by user"
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
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "table_schema": {"type": "string"},
                    "data_type": {"type": "string"},
                    "is_nullable": {"type": "string"},
                    "constraint_type": {"type": "string"},
                    "foreign_key_reference": {"type": ["string", "null"]}
                }
            }
        }
    }
    output_type = "string"
    def forward(self, query : str, context : List[dict]):
        return generate_sql_from_context(query=query, context=context, config=config.llm)["sql"]
    

agent = CodeAgent(
    model=model,
    tools=[ContextRetriever(), GenerateSqlTool(), SqlRunner()],
    additional_authorized_imports=['unicodedata', 'itertools', 'random', 'stat', 're', 
'datetime', 'statistics', 'collections', 'math', 'time', 'queue'], planning_interval=5
)

if __name__ == "__main__":
    query = "who are most valuable customer"
    response = agent.run(query)
    print(response)

