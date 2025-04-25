from core.sql_generator import generate_sql_from_context, validate_and_run_sql
from core.retreivers import get_context
from core import chat_completion_from_config
from config.config import ChatCompletionConfig
from core._database import DatabaseBase
from core.index import Index
import json
import pandas as pd



def generate_insight(query: str, sql_result, config: ChatCompletionConfig):
        if isinstance(sql_result, pd.DataFrame):
             sql_result = sql_result.to_dict(orient="records")
        prompt = f"""
        You are a data analyst. A user asked the following question:

        "{query}"

        You wrote a SQL query, and here is the result table:

        {sql_result}

        Now, analyze the result and summarize the key insights clearly and concisely. Focus on trends, patterns, anomalies, or top contributors. Use plain English suitable for a business decision-maker. If applicable, suggest one actionable takeaway.
        """
        messages= [
                    {
                        "role": "system",
                        "content": f"You are a data analyst expert.",
                    },
                    {"role": "user", "content": prompt},
                ]
        
        response = chat_completion_from_config(
                messages=messages,
                config=config,
            )
        return {
            "insight": response.choices[0].message.content
        }


class GeneratorWorkflow:
    def __init__(
        self,
        source_database: DatabaseBase,
        interal_database: DatabaseBase,
        index: Index,
        config: ChatCompletionConfig,
    ):
        self.internal_db = interal_database
        self.source_db = source_database
        self.index = index
        self.config = config

    
    def generate_insight_with_retry(self, query: str, retry: int = 3):
        context = get_context(
            query=query,
            index=self.index,
            internal_db=self.internal_db,
            source=self.source_db,
        )
        generated_sql = generate_sql_from_context(
            query=query, context=context, config=self.config
        )
        raw_sql = generated_sql["sql"]
        for attempt in range(retry):
            result, error = validate_and_run_sql(raw_sql, self.source_db)
            if not error:
                insight = generate_insight(query, result, self.config)
                return {**insight, **generated_sql,
                        "sql_result": result.to_dict(orient="records") 
                        #"context": context # commented this one because there is a bug that failed to parse nans in json api respone.
                        }, None
            if attempt < retry - 1:
                print(error)
                retry_prompt = (
                    f"The following SQL query was generated:\n\n{raw_sql}\n\n"
                    f"But it produced this error:\n\n{error}\n\n"
                    f"Please correct and regenerate a valid SQL query for the original request:\n\n{query}"
                )
                generated_sql = generate_sql_from_context(
                    query=retry_prompt, context=context, config=self.config
                )
                raw_sql = generated_sql["sql"]
            else:
                break
        return {}, "Failed to generated SQL"
