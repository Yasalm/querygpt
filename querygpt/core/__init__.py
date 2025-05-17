from querygpt.core._database import DATABASE_REGISTRY, DatabaseConfig, InternalDatabase
from querygpt.config.config import ChatCompletionConfig, Config
from pydantic import BaseModel
from typing import List
from querygpt.core.index import get_index
import json
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
from querygpt.core.memory import Memory

def init_internal_database_from_config(config: DatabaseConfig):
    return InternalDatabase(config)


def init_database_from_config(config: DatabaseConfig):
    assert (
        config.engine in DATABASE_REGISTRY
    ), f"Invalid database engine: {config.engine}, available engines: {DATABASE_REGISTRY.keys()}"
    return DATABASE_REGISTRY[config.engine](config)

@Memory()
def chat_completion_from_config(
    messages: List[str], config: ChatCompletionConfig, response_format: BaseModel = None
):
    if config.remote:
        if config.base_url:
            import httpx
            from openai import OpenAI
            from openai.lib._parsing._completions import type_to_response_format_param
            http_client = httpx.Client(trust_env=False)
            client = OpenAI(base_url=config.base_url, api_key="", http_client=http_client)
            # url = f'{config.base_url}/chat/completions'
            data = {
                    "model": config.model,
                    "messages": messages,
                    "temperature": config.temperature,
                    }
            if response_format:
                data["response_format"] = type_to_response_format_param(response_format)
            return client.chat.completions.create(**data)



        else:
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
# have to be refactored: but later
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


_EMBEDDING_COLUMNS = [
    "table_bussines_summary",
    "table_possible_usages",
    "column_name",
    "column_details_summary",
    "bussines_summary",
    "possible_usages",
    "tags",
]

_IDENTIFIER_COLUMNS = ["id", "table_id"]


def _generate_documentation(
    table_name: str, columns_data: List[dict], config: ChatCompletionConfig
) -> _TableDocumentation:
    try:
        # quick fix: for clickhouse do not have this type of infrommation, as it does not enforec foregins relationships
        new_cols = []
        for col in columns_data:
            _col = {k: v for k, v in col.items() if k != "foreign_key_table_docs"}
            if col.get("foreign_key_reference"):
                _col["foreign_key_info"] = col.get("foreign_key_reference")
            new_cols.append(_col)
    except:
        new_cols = columns_data

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


def _process_tables_schema(tables_schema: pd.DataFrame, engine: str) -> List[dict]:
    tables_dict = tables_schema.to_dict(orient="records")
    tables_schema = defaultdict(list)
    for item in tables_dict:
        if engine != 'clickhouse':
            ref = item["foreign_key_reference"]
            if ref is not None:
                ref_tab, _ = ref.split(".")
                # Find the referenced table information
                ref_table_data = [t for t in tables_dict if t["table_name"] == ref_tab]
                item["foreign_key_table_docs"] = ref_table_data
            else:
                item["foreign_key_table_docs"] = {}
        tables_schema[item["table_name"]].append(item)
    return tables_schema


def _process_docs_for_embedding(
    documenation: pd.DataFrame,
    embedding_columns: list = _EMBEDDING_COLUMNS,
    identifier_columns: list = _IDENTIFIER_COLUMNS,
) -> dict:
    """documenation is a dataframe generated from `_generate_documentation`"""
    table_docs = documenation[embedding_columns + identifier_columns].rename(
        {"id": "column_id"}, axis=1
    )
    table_docs["_text"] = table_docs.apply(
        lambda row:
        # "<table_summary>" + row["table_bussines_summary"] + "</table_summary>"
        # + "<table_possible_usages>" + row["table_possible_usages"] + "</table_possible_usages>"
        "<column_name>"
        + row["column_name"]
        + "</column_name>"
        + "<column_details_summary>"
        + row["column_details_summary"]
        + "</column_details_summary>"
        + "<column_bussines_summary>"
        + row["bussines_summary"]
        + "</column_bussines_summary>"
        + "<column_possible_usages>"
        + row["possible_usages"]
        + "</column_possible_usages>",
        axis=1,
    )
    docs = table_docs[["table_id", "column_id", "tags", "_text"]].to_dict(
        orient="records"
    )
    for doc in docs:
        tags = list(doc["tags"])
        _tags = "<tags>"
        for tag in tags:
            _tags += f"{tag},"
        _tags += "</tags"
        doc["_text"] += _tags
    return docs


def init_sources_documentation_from_config(config: Config):
    # create index
    index = get_index(config.index)
    internal_db = init_internal_database_from_config(config.internal_db)
    # i need to get all schema: Prepare for llm documentation generation
    source_dbs = [
        init_database_from_config(source.database) for source in config.sources
    ]
    for source_db in source_dbs:
        tables_schema = source_db.get_all_tables_schema()
        tables_schema = _process_tables_schema(tables_schema, source_db.engine)
        for table_name, columns_data in tqdm(
            tables_schema.items(),
            desc="generating and saving documentations...",
        ):
            documentation = _generate_documentation(
                table_name, columns_data, config.llm
            )
            internal_db.save_documentation(documentation)
        # temporary
        docs = internal_db.get_all_documenations()
        processed_docs = _process_docs_for_embedding(docs)
        # generate embedding
        payloads = [
            {
                "column_id": doc["column_id"],
                "table_id": doc["table_id"],
            }
            for doc in processed_docs
        ]
        texts = [doc["_text"] for doc in processed_docs]
        embeddings = index.embedder.embed(texts)  # Also temp :(
        index.upsert(embeddings=embeddings, payloads=payloads)
