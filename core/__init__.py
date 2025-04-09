from core._database import DATABASE_REGISTRY, DatabaseConfig, InternalDatabase
from config.config import ChatCompletionConfig, Config
from pydantic import BaseModel
from typing import List
from core.index import Index
import json
import pandas as pd
from collections import defaultdict

def init_internal_database_from_config(config: DatabaseConfig):
    return InternalDatabase(config)

def init_database_from_config(config: DatabaseConfig):
    assert (
        config.engine in DATABASE_REGISTRY
    ), f"Invalid database engine: {config.engine}, available engines: {DATABASE_REGISTRY.keys()}"
    return DATABASE_REGISTRY[config.engine](config)


def chat_completion_from_config(
    messages: List[str], config: ChatCompletionConfig, response_format: BaseModel = None
):
    if config.remote:
        from litellm import completion

        return completion(
            messages=messages,
            model=config.model,
            temperature=config.temperature,
            response_format=response_format,
        )
    else:
        raise NotImplementedError("Local LLM is not supported yet")

# must be identical to the one in the internal db schema file
class _ColumnDocumentation(BaseModel):
    column_name: str
    column_details_summary: str
    bussines_summary: str
    possible_usages: str
    tags: list[str]


class _TableDocumentation(BaseModel):
    table_name: str
    bussines_summary: str
    possible_usages: str
    columns_summary: list[_ColumnDocumentation]


def _generate_documentation(
    table_name: str, columns_data: List[dict], config: ChatCompletionConfig
) -> _TableDocumentation:
    new_cols = []
    for col in columns_data:
        _col = {k: v for k, v in col.items() if k != "foreign_key_table_metadata"}
        if col.get("foreign_key_reference"):
            _col["foreign_key_info"] = col.get("foreign_key_reference")
        new_cols.append(_col)

    prompt = f"""
        I need comprehensive documentation for a database table named '{table_name}' with the following columns:
        
        {json.dumps(new_cols, indent=2)}
        
        For each table, provide:
        1. A business summary explaining the purpose and role of the table
        2. Possible usage scenarios for the table
        
        For each column, provide:
        1. A detailed summary of what the column represents
        2. A business summary explaining the significance of this data
        3. Possible usage scenarios for this column
        4. A list of relevant tags (e.g., identifier, text, timestamp, foreign key, etc.)
    """

    messages = [
        {
            "role": "system",
            "content": "You are a data documentation expert.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = chat_completion_from_config(
            messages, config, response_format=_TableDocumentation
        )
        return _TableDocumentation(**json.loads(response.choices[0].message.content))
    except Exception as e:
        raise e


def _process_tables_schema(tables_schema: pd.DataFrame) -> List[dict]:
    tables_dict = tables_schema.to_dict(orient="records")
    tables_schema = defaultdict(list)
    for item in tables_dict:
        ref = item["foreign_key_reference"]
        if ref is not None:
            ref_tab, _ = ref.split(".")
            # Find the referenced table information
            ref_table_data = [t for t in tables_dict if t["table_name"] == ref_tab]
            item["foreign_key_table_metadata"] = ref_table_data
        else:
            item["foreign_key_table_metadata"] = {}
        tables_schema[item["table_name"]].append(item)
    return tables_schema


def init_sources_documentation_from_config(config: Config):
    # create index
    index = Index(config.index)
    internal_db = init_internal_database_from_config(config.internal_db)
    # i need to get all schema: Prepare for llm documentation generation
    source_dbs = [
        init_database_from_config(source.database) for source in config.sources
    ]
    for source_db in source_dbs:
        tables_schema = source_db.get_all_tables_schema()
        tables_schema = _process_tables_schema(tables_schema)
        for table_name, columns_data in tables_schema.items():
            documentation = _generate_documentation(
                table_name, columns_data, config.llm
            )
            # save to internal db
            internal_db.save_documentation(documentation)
            # prepare for embedding
            # generate embedding
            # save to index with payload as list(list(emebdding:float)), list[payload:dict]
            break
        print(type(documentation))
        # prepare for llm documentation generation
        # upsert to index
        # save to internal db

    # loop over sources
    # get schema
    # prepare for llm documentation generation
    # upsert to index
    # save to internal db
