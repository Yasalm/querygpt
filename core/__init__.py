from core._database import DATABASE_REGISTRY, DatabaseConfig
from config.config import ChatCompletionConfig, Config
from pydantic import BaseModel
from typing import List

def init_database_from_config(config: DatabaseConfig):
    assert config.engine in DATABASE_REGISTRY, f"Invalid database engine: {config.engine}, available engines: {DATABASE_REGISTRY.keys()}"
    return DATABASE_REGISTRY[config.engine](config)

def chat_completion_from_config(messages: List[str], config: ChatCompletionConfig, response_format: BaseModel = None):
    if not config.local:
        from litellm import completion
        return completion(messages=messages, model=config.model, temperature=config.temperature, response_format=response_format)
    else:
        raise NotImplementedError("Local LLM is not supported yet")

def init_sources_documentation_from_config(config: Config):
    # create index
    # loop over sources
    # get schema
    # prepare for llm documentation generation
    # upsert to index
    # save to internal db
    pass