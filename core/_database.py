from psycopg2 import connect
import duckdb
from contextlib import contextmanager
from enum import Enum
from config.config import DatabaseConfig
from pathlib import Path
import os
import pandas as pd
from typing import List


def resolve_path_from_project(relative_path: str) -> Path:
    return Path(__file__).resolve().parent.parent / relative_path.lstrip("/")


def load_query_from_file(query_path: str) -> str:
    with open(query_path, "r") as file:
        return "".join(file.readlines())


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

    def list_all_schemas(self):
        raise NotImplementedError()

    def list_all_tables(self):
        raise NotImplementedError()

    def list_all_columns(self, table_name: str):
        raise NotImplementedError()

    def execute_query(self, query: str):
        raise NotImplementedError()

    def get_all_tables_schema(self):
        raise NotImplementedError()

    def get_table_schema(self, table_name: str):
        raise NotImplementedError()

    def get_table_sample_data(self, table_name: str):
        raise NotImplementedError()


class PostgresDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    @contextmanager
    def connect(self):
        conn_params = {
            k: v
            for k, v in vars(self.config).items()
            if k != "engine" and v is not None and k != "schema_query_path"
        }
        conn = connect(**conn_params)
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, as_dataframe: bool = True):
        with self.connect() as conn:
            if as_dataframe:
                return pd.read_sql_query(query, conn)
            else:
                return conn.execute(query)

    def list_all_schemas(
        self, exclude_system_schemas: List[str] = ["information_schema", "pg_catalog"]
    ):
        return self.execute_query(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
            )
        )

    def list_all_tables(
        self, exclude_system_schemas: List[str] = ["information_schema", "pg_catalog"]
    ):
        return self.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
            )
        )

    def list_all_columns(
        self,
        table_name: str,
        exclude_system_schemas: List[str] = ["information_schema", "pg_catalog"],
    ):
        return self.execute_query(
            "SELECT column_name FROM information_schema.columns WHERE table_name = '{}' AND table_schema NOT IN ({})".format(
                table_name,
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas),
            )
        )

    def get_all_tables_schema(self):
        path = resolve_path_from_project(self.config.schema_query_path)
        query = load_query_from_file(path)
        return self.execute_query(query)

    def get_table_schema(self, table_name: str):
        all_tables_schema = self.get_all_tables_schema()
        return all_tables_schema[all_tables_schema["table_name"] == table_name]

    def get_table_sample_data(self, table_name: str):
        return self.execute_query("select * from {} limit 10".format(table_name))


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


class InternalDatabase(DuckDBDatabase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)


DATABASE_REGISTRY = {
    DatabaseEngine.POSTGRES.value: PostgresDatabase,
    DatabaseEngine.DUCKDB.value: DuckDBDatabase,
}
