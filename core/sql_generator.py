from core import chat_completion_from_config
from typing import List
import numpy as np
from pydantic import BaseModel
from config.config import ChatCompletionConfig
import json
from core._database import DatabaseBase

class SQLModel(BaseModel):
    sql: str
    explanation: str
    relevant_sources_from_context: str


def generate_sql_from_context(query: str, context: List[dict], database : str, config: ChatCompletionConfig):
        # quick fix for numpy array, should be fixed in the source
        context = [item.tolist() if isinstance(item, np.ndarray) else item for item in context]
        prompt = f"""
        You are a SQL expert tasked with generating a SQL query based on a natural language question.

        CONTEXT:
        {context}

        DATABASE: {database}

        INSTRUCTIONS:
        1. Generate a SQL query that answers the following question: "{query}"
        2. Use only tables and columns that are mentioned in the CONTEXT section.
        3. Make sure your query is syntactically correct and follows best practices for {database}.
        4. Include appropriate JOINs when querying across multiple tables.
        5. Add comments to explain your reasoning for complex parts of the query.
        6. If the question cannot be answered with the available tables/columns, explain why.

        Your response should be structured as follows:

        SQL:
        [Your SQL query here]

        EXPLANATION:
        [Your explanation of how the query works and any assumptions made]

        RELEVANT SOURCES FROM CONTEXT:
        [Your derived infromation from the context provided]
        """
        messages= [
                    {
                        "role": "system",
                        "content": f"You are a {database} database expert.",
                    },
                    {"role": "user", "content": prompt},
                ]
        
        response = chat_completion_from_config(
                messages=messages,
                config=config,
                response_format=SQLModel,
            )
         
        return json.loads(response.choices[0].message.content)


def validate_and_run_sql(sql : str, database: DatabaseBase):
      """Evalutate and run sql query"""
      try:
           result = database.execute_query(query=sql)
           return result, None
      except Exception as e:
            return None, str(e)

# def validate_and_run_sql(self, sql: str):
#         """Extract SQL tables and columns from SQL query and check if they are in the source."""
#         parsed = sqlparse.parse(sql)
#         table_names = set() 

#         for statement in parsed:
#             from_seen = False
#             for token in statement.tokens:
#                 if token.ttype is DML and token.value.upper() == 'SELECT':
#                     continue  
#                 if token.ttype is Keyword and token.value.upper() in ['FROM', 'JOIN']:
#                     from_seen = True
#                 elif from_seen:
#                     if isinstance(token, IdentifierList):
#                         for identifier in token.get_identifiers():
#                             table_names.add(identifier.get_real_name())
#                     elif isinstance(token, Identifier):
#                         table_names.add(token.get_real_name())
#                     elif token.ttype is Keyword and token.value.upper() == 'WHERE':
#                         break
#         for table in list(table_names):
#             # can be re-done also also include column-table mapping checks                 
#             try:
#                 _ = self.source_db.execute_query(f"select * from {table}")
#             except Exception as e:# if any table is not in the source, FAILS
#                 return False, [table]
#         return True, list(table_names)