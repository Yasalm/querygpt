from psycopg2 import connect
import duckdb
from contextlib import contextmanager
from enum import Enum
from config.config import DatabaseConfig, init_config
from pathlib import Path
import os

def resolve_path_from_project(relative_path: str) -> Path:
    return Path(__file__).resolve().parent.parent / relative_path.lstrip("/")

class DatabaseEngine(Enum):
    POSTGRES = "postgres"
    DUCKDB = "duckdb"

class DatabaseBase:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = config.engine

    @contextmanager
    def connect(self):
        raise NotImplementedError()

class PostgresDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
    @contextmanager
    def connect(self):
        conn_params = {k: v for k, v in vars(self.config).items() 
                      if k != 'engine' and v is not None}
        conn = connect(**conn_params)
        try:
            yield conn
        finally:
            conn.close()

class DuckDBDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
    @contextmanager
    def connect(self):
        path = self.config.path
        path = resolve_path_from_project(path)
        os.makedirs(path.parent, exist_ok=True)
        conn = duckdb.connect(path)
        try:
            yield conn
        finally:
            conn.close()

DATABASE_REGISTRY = {
    DatabaseEngine.POSTGRES.value: PostgresDatabase,
    DatabaseEngine.DUCKDB.value: DuckDBDatabase,
}

