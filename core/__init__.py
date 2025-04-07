from core._database import DATABASE_REGISTRY, DatabaseConfig

def init_database_from_config(config: DatabaseConfig):
    assert config.engine in DATABASE_REGISTRY, f"Invalid database engine: {config.engine}, available engines: {DATABASE_REGISTRY.keys()}"
    return DATABASE_REGISTRY[config.engine](config)