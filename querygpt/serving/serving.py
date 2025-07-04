# WP
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
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
from querygpt import Agent
from querygpt.core.logging import get_logger
import json

logger = get_logger(__name__)

# config = init_config()
# # # init_sources_documentation_from_config(config) # this should be moved to a diff script before running the serving api
# # source_dbs = [init_database_from_config(source.database) for source in config.sources]
# # source_db = source_dbs[0]  # TMP: as we only support one source for now.
# # internal_db = init_internal_database_from_config(config.internal_db)
# # index = get_index(config.index)

# # workflow = GeneratorWorkflow(source_database=source_db, interal_database=internal_db, index=index, config=config.llm)

app = FastAPI()
logger.info("Initializing FastAPI application")
agent = Agent()
logger.info("Agent initialized successfully")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatResponse(BaseModel):
    content: str


@app.get("/history")
def get_history():
    logger.info("History endpoint called")
    return {"history"}


@app.post(
    "/chat",
)
def get_chat(query: str):
    logger.info(f"Chat endpoint called with query: {query[:100]}...")
    # agent = create_agent(task="query")
    # final_answer = agent.run(query)
    # sql_result = None
    # sql_gen = None
    # insight = None

    # if final_answer and hasattr(agent.tools["validate_sql_and_exceute_it"], "_final"):
    #     sql_result = agent.tools["validate_sql_and_exceute_it"]._final

    # if final_answer and hasattr(agent.tools["sql_generator"], "_final"):
    #         sql_gen = agent.tools["sql_generator"]._final

    # if final_answer and hasattr(agent.tools["generate_insghits_from_sql_result"], "_final"):
    #     insight = agent.tools["generate_insghits_from_sql_result"]._final

    # if sql_gen and not insight:
    #     insight = generate_insight(
    #             query=query, sql_result=sql_result, config=config.llm
    #         )

    # final_answer = final_answer.to_string() if hasattr(final_answer, "to_string") else final_answer

    # response = {"agent_answer": final_answer, **(sql_gen or {}), **(insight or {})}

    # if sql_result and isinstance(sql_result, list):
    #     if len(sql_result) >= 10:
    #         response["sql_result_sample"] = sql_result[:2]
    #     else:
    #         response["sql_result"] = sql_result
    try:
        logger.debug("Starting agent run with trace")
        trace = agent.run_with_trace(query, use_enhanced_task=True)
        final_answer = trace.final_answer
        final_answer = json.loads(final_answer)
        logger.info("Chat request completed successfully")
        return final_answer
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "querygpt.serving.serving:app", host="127.0.0.1", port=8000, reload=True
    )
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
