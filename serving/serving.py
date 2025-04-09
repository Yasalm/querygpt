import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
import uvicorn
from config.config import init_config
from core.index import Index
from core import init_database_from_config, init_sources_documentation_from_config, init_internal_database_from_config

config = init_config()
source_dbs = [init_database_from_config(source.database) for source in config.sources]
if __name__ == "__main__":
    # init_sources_documentation_from_config(config)
    internal_db = init_internal_database_from_config(config.internal_db)
    print(internal_db.execute_query("SELECT * FROM table_metadata"))