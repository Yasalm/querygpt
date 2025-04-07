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


class DatabaseConfig(BaseModel):
    engine: str


class PostgresDatabaseConfig(DatabaseConfig):
    user: str
    password: str
    host: str
    port: int
    dbname: str
    schema_query_path: str


class DuckDBDatabaseConfig(DatabaseConfig):
    path: str


class SourceConfig(BaseModel):
    name: str
    database: DatabaseConfig


class Config(BaseModel):
    index: IndexConfig
    sources: List[SourceConfig]
    internal_db: DuckDBDatabaseConfig


def init_config():
    from dotenv import load_dotenv
    from omegaconf import OmegaConf
    import os
    import warnings

    load_dotenv()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        OmegaConf.register_resolver("env", lambda key: os.environ.get(key))

    config = OmegaConf.load("config/config.yaml")

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
            else:
                raise ValueError(f"Unknown engine: {engine}")

            source_config["database"] = db_obj

        sources_list.append(SourceConfig(**source_config))

        resolved_config["sources"] = sources_list

    return Config(**resolved_config)

