from contextlib import contextmanager
from enum import Enum
from querygpt.config.config import DatabaseConfig
from pathlib import Path
import os
import pandas as pd
from typing import List, Union
import json
from pathlib import Path
from querygpt.core.trace import Trace

def resolve_path_from_project(relative_path: str) -> Path:
    return Path(__file__).resolve().parent.parent / relative_path.lstrip("/")


def load_query_from_file(query_path: str) -> str:
    with open(query_path, "r") as file:
        return "".join(file.readlines())


class DatabaseEngine(Enum):
    POSTGRES = "postgres"
    DUCKDB = "duckdb"
    CLICKHOUSE = "clickhouse"
    ORACLE = "oracle"


class DatabaseBase:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = config.engine

    @contextmanager
    def connect(self):
        raise NotImplementedError()

    def list_all_schemas(self, *args, **kwargs):
        raise NotImplementedError()

    def list_all_tables(self, *args, **kwargs):
        raise NotImplementedError()

    def list_all_columns(self, *args, **kwargs):
        raise NotImplementedError()

    def execute_query(
        self,
        query: str,
        as_dataframe: bool = True,
    ):
        with self.connect() as conn:
            if as_dataframe:
                return pd.read_sql_query(query, conn)
            else:
                return conn.execute(query)

    def get_all_tables_schema(self, *args, **kwargs):
        raise NotImplementedError()

    def get_table_schema(self, *args, **kwargs):
        raise NotImplementedError()

    def get_table_sample_data(self, *args, **kwargs):
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
        try:
            from psycopg2 import connect
        except ImportError as e:
            raise ModuleNotFoundError(
                "To use Postgres, please install psycopg2 by using 'pip install querygpt[postgres]'"
            )
        conn = connect(**conn_params)
        try:
            yield conn
        finally:
            conn.close()

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
        table_schema: str = None,
        table_name: str = None,
        exclude_system_schemas: List[str] = ["information_schema", "pg_catalog"],
    ):
        if table_name:
            # table = f'{table_schema}.{table_name}'
            table = table_name
            return self.execute_query(
                "SELECT column_name FROM information_schema.columns WHERE table_name = '{}' AND table_schema NOT IN ({})".format(
                    table,
                    ", ".join(f"'{schema}'" for schema in exclude_system_schemas),
                )
            )
        return self.execute_query(
            "SELECT column_name FROM information_schema.columns WHERE table_schema NOT IN ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas),
            )
        )

    def get_all_tables_schema(self):
        path = resolve_path_from_project(self.config.schema_query_path)
        query = load_query_from_file(path)
        return self.execute_query(query)

    def get_table_schema(self, table_name: Union[str, List[str]]):
        table_names = [table_name] if isinstance(table_name, str) else table_name
        all_tables_schema = self.get_all_tables_schema()
        return all_tables_schema[all_tables_schema["table_name"].isin(table_names)]

    def get_table_sample_data(self, table_schema: str, table_name: str):
        if table_name and table_schema:
            table = f"{table_schema}.{table_name}"
            return self.execute_query("select * from {} limit 10".format(table))
        return ValueError(
            f"both table_schema: {table_schema}, and table_name {table_name} cannot be null"
        )


class OracleDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    @contextmanager
    def connect(self):
        try:
            from oracledb import connect
        except ImportError as e:
            raise ModuleNotFoundError(
                "To use Oracle, please install oracledb by using 'pip install querygpt[oracle]'"
            )

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

    def list_all_schemas(
        self,
        exclude_system_schemas: List[str] = [
            "SYS",
            "SYSTEM",
            "C##DBA_YAA",
            "CTXSYS",
            "DBSNMP",
            "DVSYS",
            "GSMADMIN_INTERNAL",
            "LBACSYS",
            "MDSYS",
            "OLAPSYS",
            "ORDDATA",
            "ORDSYS",
            "OUTLN",
            "WMSYS",
            "XDB",
        ],
    ):
        return self.execute_query(
            "SELECT username as schema_name FROM all_users WHERE username in ('FRAUD_USR', 'COLL_USR')"
        )

    def list_all_tables(
        self,
        exclude_system_schemas: List[str] = [
            "SYS",
            "SYSTEM",
            "C##DBA_YAA",
            "CTXSYS",
            "DBSNMP",
            "DVSYS",
            "GSMADMIN_INTERNAL",
            "LBACSYS",
            "MDSYS",
            "OLAPSYS",
            "ORDDATA",
            "ORDSYS",
            "OUTLN",
            "WMSYS",
            "XDB",
        ],
    ):
        return self.execute_query(
            """SELECT owner as schema_name,
       table_name
FROM   all_tables     
where owner in  ('FRAUD_USR', 'COLL_USR')   
ORDER  BY owner, table_name 
            """
        )

    def list_all_columns(
        self,
        table_schema: str = None,
        table_name: str = None,
        exclude_system_schemas: List[str] = ["information_schema", "pg_catalog"],
    ):
        if table_name:
            # table = f'{table_schema}.{table_name}'
            table = table_name
            return self.execute_query(
                """SELECT owner schema_name,
                        table_name,
                        column_name,
                        data_type,
                        data_length,
                        data_precision,
                        data_scale,
                        nullable
                    FROM   all_tab_columns
                    where table table_name = '{}'        
                    ORDER  BY owner, table_name, column_id
                """.format(
                    table
                )
            )
        return self.execute_query(
            """SELECT owner schema_name,
                        table_name,
                        column_name,
                        data_type,
                        data_length,
                        data_precision,
                        data_scale,
                        nullable
                    FROM   all_tab_columns
                    ORDER  BY owner, table_name, column_id"""
        )

    def get_all_tables_schema(self):
        path = resolve_path_from_project(self.config.schema_query_path)
        query = load_query_from_file(path)
        return self.execute_query(query)

    def get_table_schema(self, table_name: Union[str, List[str]]):
        table_names = [table_name] if isinstance(table_name, str) else table_name
        all_tables_schema = self.get_all_tables_schema()
        return all_tables_schema[all_tables_schema["TABLE_NAME"].isin(table_names)]

    def get_table_sample_data(self, table_schema: str, table_name: str):
        if table_name and table_schema:
            table = f"{table_schema}.{table_name}"
            return self.execute_query(
                "select * from {} where rownum <= 10".format(table)
            )
        return ValueError(
            f"both table_schema: {table_schema}, and table_name {table_name} cannot be null"
        )


class ClickhouseDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    @contextmanager
    def connect(self):
        try:
            from sqlalchemy import create_engine
            from clickhouse_sqlalchemy import make_session
        except ImportError  as e:
            raise ModuleNotFoundError(
                "To use Clickhouse, please install clickhouse-sqlalchemy and sqlalchemy by using 'pip install querygpt[clickhouse]'"
            )

        engine = create_engine(
            f"clickhouse://{self.config.user}:{self.config.password}@{self.config.host}/{self.config.dbname}"
        )
        session = make_session(engine)
        try:
            yield session.bind
        finally:
            session.close()

    def list_all_schemas(
        self,
        exclude_system_schemas: List[str] = [
            "system",
            "information_schema",
            "INFORMATION_SCHEMA",
        ],
    ):
        return self.execute_query(
            "select distinct database as table_schemas from system.columns where database not in ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
            )
        )

    def list_all_tables(
        self,
        exclude_system_schemas: List[str] = [
            "system",
            "information_schema",
            "INFORMATION_SCHEMA",
        ],
    ):
        return self.execute_query(
            "select distinct database as table_schemas, table AS table_name from system.columns where database not in ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
            )
        )

    def list_all_columns(
        self,
        table_schema: str = None,
        table_name: str = None,
        exclude_system_schemas: List[str] = [
            "system",
            "information_schema",
            "INFORMATION_SCHEMA",
        ],
    ):
        if table_name and table_schema:
            table = f"{table_schema}.{table_name}"
            return self.execute_query(
                "select distinct table AS table_name, name AS column_name from system.columns where table = {} database not in ({})".format(
                    table, ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
                )
            )
        return self.execute_query(
            "select distinct name AS column_name from system.columns where database not in ({})".format(
                ", ".join(f"'{schema}'" for schema in exclude_system_schemas)
            )
        )

    def get_all_tables_schema(self):
        path = resolve_path_from_project(self.config.schema_query_path)
        query = load_query_from_file(path)
        return self.execute_query(query)

    def get_table_schema(self, table_name: Union[str, List[str]]):
        table_names = [table_name] if isinstance(table_name, str) else table_name
        all_tables_schema = self.get_all_tables_schema()
        return all_tables_schema[all_tables_schema["table_name"].isin(table_names)]

    def get_table_sample_data(self, table_schema: str, table_name: str):
        if table_name and table_schema:
            table = f"{table_schema}.{table_name}"
        return self.execute_query("select * from {} limit 10".format(table))


class DuckDBDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    @contextmanager
    def connect(self):
        try:
            from duckdb import connect
        except ImportError as e:
            raise ModuleNotFoundError(
                "To use DuckDB, please install duckdb by using 'pip install querygpt[duckdb]'"
            )
        # path = resolve_path_from_project(self.config.path)
        path = Path(self.config.path)
        os.makedirs(path.parent, exist_ok=True)
        conn = connect(path)
        try:
            yield conn
        finally:
            conn.close()


class InternalDatabase(DuckDBDatabase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.__post_init__()

    def __post_init__(self):
        # post init is to do checks on interal ddl scheam
        try:
            path = resolve_path_from_project(self.config.ddl_query_path)
            ddl_script = load_query_from_file(path)
            with self.connect() as conn:
                conn.execute(ddl_script)
        except Exception as e:
            raise e
        
    def save_trace(self, trace: Trace):
        """Save the trace into the database.
        
        Args:
            trace (Trace): The trace to save.
            
        Returns:
            trace_id (int): The id of the trace.
        """
        trace = trace.to_dict()
        try:
            with self.connect() as conn:
                trace_id = conn.execute(
                    "INSERT INTO trace (id, task, enhanced_task, start_time, end_time, duration_seconds, final_answer, system_prompt, total_steps) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                    (
                        trace.get("id"),
                        trace.get("task"),
                        trace.get("enhanced_task"),
                        trace.get("start_time"),
                        trace.get("end_time"),
                        trace.get("duration_seconds"),
                        trace.get("final_answer"),
                        trace.get("system_prompt"),
                        trace.get("total_steps")
                    ),
                ).fetchone()
                trace_id = trace_id[0]
                for step in trace["steps"]:
                    conn.execute(
                        "INSERT INTO tracestep (id, trace_id, step_number, step_type, start_time, end_time, duration_seconds, model_input, model_output, tool_calls, observations, error, action_output, plan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            step.get("id"),
                            step.get("trace_id"),
                            step.get("step_number"),
                            step.get("step_type"),
                            step.get("start_time"),
                            step.get("end_time"),
                            step.get("duration_seconds"),
                            step.get("model_input"),
                            step.get("model_output"),
                            step.get("tool_calls"),
                            step.get("observations"),
                            step.get("error"),
                            step.get("action_output"),
                            step.get("plan")
                        ),
                    )
            return trace_id
        except Exception as e:
            raise e
        
    def save_documentation(self, documentation):
        documentation = documentation.model_dump()
        with self.connect() as conn:
            # should be a standalone function that can be used for all tables to check if documentation exists, if not then run init_documentation. but we can ignore for now..
            table_id = conn.execute(
                "SELECT id FROM table_metadata WHERE table_name = ?",
                (documentation["table_name"],),
            ).fetchone()

            if table_id:
                conn.execute(
                    """
                    UPDATE table_metadata 
                    SET bussines_summary = ?, possible_usages = ?
                    WHERE id = ?
                    """,
                    (
                        documentation["bussines_summary"],
                        documentation["possible_usages"],
                        table_id[0],
                    ),
                )
            else:
                table_id = conn.execute(
                    """
                    INSERT INTO table_metadata (table_name, bussines_summary, possible_usages)
                    VALUES (?, ?, ?)
                    RETURNING id
                    """,
                    (
                        documentation["table_name"],
                        documentation["bussines_summary"],
                        documentation["possible_usages"],
                    ),
                ).fetchone()

            table_id = table_id[0]

            for column in documentation["columns_summary"]:
                column_id = conn.execute(
                    """
                SELECT id FROM column_metadata 
                WHERE table_id = ? AND column_name = ?
                """,
                    (table_id, column["column_name"]),
                ).fetchone()

                if column_id:
                    conn.execute(
                        """
                        UPDATE column_metadata 
                        SET column_details_summary = ?, 
                            bussines_summary = ?, 
                            possible_usages = ?, 
                            tags = ?
                        WHERE id = ?
                        """,
                        (
                            column["column_details_summary"],
                            column["bussines_summary"],
                            column["possible_usages"],
                            json.dumps(column["tags"]),
                            column_id[0],
                        ),
                    )
                else:
                    column_id = conn.execute(
                        """
                        INSERT INTO column_metadata 
                        (table_id, column_name, column_details_summary, bussines_summary, possible_usages, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                        RETURNING id
                        """,
                        (
                            table_id,
                            column["column_name"],
                            column["column_details_summary"],
                            column["bussines_summary"],
                            column["possible_usages"],
                            json.dumps(column["tags"]),
                        ),
                    ).fetchone()
        return table_id

    def get_all_documenations(self, as_dataframe: bool = True):
        query = """select t.id table_id, t.table_name, t.bussines_summary table_bussines_summary, t.possible_usages table_possible_usages, c.*
                from column_metadata c, table_metadata t, 
                where t.id = c.table_id"""
        return self.execute_query(query, as_dataframe)

    def get_documenation(
        self, table_ids: List[int], column_ids: List[int], as_dataframe: bool = True
    ):
        query = f"""select t.id table_id, t.table_name, t.bussines_summary table_bussines_summary, t.possible_usages table_possible_usages, c.*
                from column_metadata c, table_metadata t, 
                where c.id in {tuple(column_ids)} and c.table_id in {tuple(table_ids)}
                and t.id = c.table_id"""
        return self.execute_query(query, as_dataframe)


DATABASE_REGISTRY = {
    DatabaseEngine.POSTGRES.value: PostgresDatabase,
    DatabaseEngine.DUCKDB.value: DuckDBDatabase,
    DatabaseEngine.CLICKHOUSE.value: ClickhouseDatabase,
    DatabaseEngine.ORACLE.value: OracleDatabase,
}
