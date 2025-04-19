import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from core import chat_completion_from_config
from core.retreivers import get_context
from core.sql_generator import generate_sql_from_context, validate_and_run_sql

from fastapi import FastAPI
import uvicorn
from config.config import init_config
from core.index import Index
from core import (
    init_database_from_config,
    init_sources_documentation_from_config,
    init_internal_database_from_config,
)
from core.retreivers import get_context
from core.workflow import GeneratorWorkflow

config = init_config()
# init_sources_documentation_from_config(config) # this should be moved to a diff script before running the serving api
source_dbs = [init_database_from_config(source.database) for source in config.sources]
source_db = source_dbs[0]  # TMP: as we only support one source for now.
internal_db = init_internal_database_from_config(config.internal_db)
index = Index(config.index)

workflow = GeneratorWorkflow(source_database=source_db, interal_database=internal_db, index=index, config=config.llm)

app = FastAPI()


class ChatResponse(BaseModel):
    content: str


@app.get("/history")
def get_history():
    return {"history"}


@app.get(
    "/chat",
)
def get_chat(query: str):
    message = {"role": "user", "content": query}

    result, error = workflow.generate_insight_with_retry(query=query, retry=5)
    if not error:
        return result
    return {
        "error": error
    }


if __name__ == "__main__":
    uvicorn.run("serving:app", host="127.0.0.1", port=8000, reload=True)
#     print(get_context(query=query, index=index, internal_db=internal_db, source=source_dbs[0]))
#     # internal_db = init_internal_database_from_config(config.internal_db)
#     # print(internal_db.execute_query("SELECT * FROM table_metadata"))
#     # print(internal_db.execute_query("SELECT count(*) FROM column_metadata"))
#     # print(source_dbs[0].get_table_schema("actor"))
