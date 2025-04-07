import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
import uvicorn
from config.config import init_config
from core.index import Index
from core import init_database_from_config

config = init_config()
internal_db = init_database_from_config(config.internal_db)
source_dbs = [init_database_from_config(source.database) for source in config.sources]
if __name__ == "__main__":
    print(source_dbs[0].get_all_tables_schema())