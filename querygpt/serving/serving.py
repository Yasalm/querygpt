#WP
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from fastapi import FastAPI
import uvicorn
from querygpt.config.config import init_config
from querygpt.core.index import get_index
from querygpt.core import (
    init_database_from_config,
    init_sources_documentation_from_config,
    init_internal_database_from_config,
)
from querygpt.core.retreivers import get_context
from querygpt.core.workflow import GeneratorWorkflow, generate_insight
from querygpt.core.agent import create_agent

config = init_config()
# init_sources_documentation_from_config(config) # this should be moved to a diff script before running the serving api
source_dbs = [init_database_from_config(source.database) for source in config.sources]
source_db = source_dbs[0]  # TMP: as we only support one source for now.
internal_db = init_internal_database_from_config(config.internal_db)
index = get_index(config.index)

workflow = GeneratorWorkflow(source_database=source_db, interal_database=internal_db, index=index, config=config.llm)

app = FastAPI()


class ChatResponse(BaseModel):
    content: str


@app.get("/history")
def get_history():
    return {"history"}


@app.get(
    "/query",
)
def get_query(query: str):
    agent = create_agent(task="query")
    final_answer = agent.run(query)
    sql_result = None
    sql_gen = None
    insight = None

    if final_answer and hasattr(agent.tools["validate_sql_and_exceute_it"], "_final"):
        sql_result = agent.tools["validate_sql_and_exceute_it"]._final

    if final_answer and hasattr(agent.tools["sql_generator"], "_final"):
            sql_gen = agent.tools["sql_generator"]._final

    if final_answer and hasattr(agent.tools["generate_insghits_from_sql_result"], "_final"):
        insight = agent.tools["generate_insghits_from_sql_result"]._final

    if sql_gen and not insight:
        insight = generate_insight(
                query=query, sql_result=sql_result, config=config.llm
            )

    final_answer = final_answer.to_string() if hasattr(final_answer, "to_string") else final_answer
        
    response = {"agent_answer": final_answer, **(sql_gen or {}), **(insight or {})}

    if sql_result and isinstance(sql_result, list):
        if len(sql_result) >= 10:
            response["sql_result_sample"] = sql_result[:2]
        else:
            response["sql_result"] = sql_result
    return response


if __name__ == "__main__":
    uvicorn.run("serving:app", host="127.0.0.1", port=8000, reload=True)
    # source_dbs = [init_database_from_config(source.database) for source in config.sources]
    # source_db = source_dbs[0]  # TMP: as we only support one source for now.
    # print(source_db.get_table_sample_data("public", "film_list"))
    # print(source_db.list_all_columns())
    # print(source_db.get_all_tables_schema())
    # print(source_db.engine)

    # # init_sources_documentation_from_config(config) # this should be moved to a diff script before running the serving api

    # # print(get_context(query="who is the most valuabe customer", index=index, internal_db=internal_db, source=source_dbs[0]))
    # internal_db = init_internal_database_from_config(config.internal_db)
    # print(internal_db.execute_query("SELECT * FROM table_metadata"))
    # print(internal_db.execute_query("SELECT * FROM column_metadata"))


#     # print(source_dbs[0].get_table_schema("actor"))
