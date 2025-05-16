from pydantic import BaseModel, Field
from typing import List


class EmbeddingModelConfig(BaseModel):
    name: str
    dimensions: int
    provider: str


class IndexConfig(BaseModel):
    name: str = Field(description="The name of the index")
    embedding_model: EmbeddingModelConfig = Field(
        description="The configuration of the embedding model used with this collection"
    )
    url: str = Field(description="The URL of the Qdrant instance")
    local: bool = Field(description="use local file for stroing index")


class DatabaseConfig(BaseModel):
    engine: str = Field(description="The engine of the database")


class PostgresDatabaseConfig(DatabaseConfig):
    user: str = Field(description="The user of the database")
    password: str = Field(description="The password of the database")
    host: str = Field(description="The host of the database")
    port: int = Field(description="The port of the database")
    dbname: str = Field(description="The name of the database")
    schema_query_path: str = Field(description="The path to the schema query file")

class ClickhouseDatabaseConfig(DatabaseConfig):
    user: str = Field(description="The user of the database")
    password: str = Field(description="The password of the database")
    host: str = Field(description="The host of the database")
    port: int = Field(description="The port of the database")
    dbname: str = Field(description="The name of the database")
    schema_query_path: str = Field(description="The path to the schema query file")

class OracleDatabaseConfig(DatabaseConfig):
    user: str = Field(description="The user of the database")
    password: str = Field(description="The password of the database")
    dsn: str = Field(description="DSN of the database, host,port")
    schema_query_path: str = Field(description="The path to the schema query file")

class DuckDBDatabaseConfig(DatabaseConfig):
    path: str = Field(description="The path to the DuckDB database file")
    ddl_query_path: str = Field(description="The path to the ddl query file")

class SourceConfig(BaseModel):
    name: str = Field(description="The name of the source")
    database: DatabaseConfig = Field(description="The configuration of the database of the source")

class ChatCompletionConfig(BaseModel):
    model: str = Field(description="The model of the chat completion")
    provider: str = Field(description="The provider of the chat completion")
    remote: bool = Field(description="Whether the chat completion is remote")
    temperature: float = Field(description="The temperature of the chat completion")
    base_url : str | None = Field(description="the base url of LLM model")


class Config(BaseModel):
    index: IndexConfig = Field(description="The configuration of the index")    
    sources: List[SourceConfig] = Field(description="The list of sources")
    internal_db: DuckDBDatabaseConfig = Field(description="The configuration of the internal database")
    llm: ChatCompletionConfig = Field(description="The configuration of the chat completion")


def init_config():
    from dotenv import load_dotenv, find_dotenv
    from omegaconf import OmegaConf
    import os
    import warnings

    load_dotenv(find_dotenv())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        if not OmegaConf.has_resolver("env"):
            OmegaConf.register_resolver("env", lambda key: os.environ.get(key))

    config = OmegaConf.load("querygpt/config/config.yaml")

    resolved_config = OmegaConf.to_container(config, resolve=True)

    if "sources" in resolved_config and isinstance(resolved_config["sources"], dict):
        sources_list = []
        for name, source_config in resolved_config["sources"].items():
            source_config["name"] = name
            engine = source_config.get("engine")

            if engine == "postgres":
                db_obj = PostgresDatabaseConfig(**source_config)
            elif engine == "duckdb":
                db_obj = DuckDBDatabaseConfig(**source_config)
            elif engine == "clickhouse":
                db_obj = ClickhouseDatabaseConfig(**source_config)
            elif engine == "oracle":
                db_obj = OracleDatabaseConfig(**source_config)
            else:
                raise ValueError(f"Unknown engine: {engine}")

            source_config["database"] = db_obj

            sources_list.append(SourceConfig(**source_config))

        resolved_config["sources"] = sources_list

    return Config(**resolved_config)

