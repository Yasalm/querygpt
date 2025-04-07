from core._database import DATABASE_REGISTRY, DatabaseConfig

def init_database_from_config(config: DatabaseConfig):
    if config.engine not in DATABASE_REGISTRY:
        raise ValueError(f"Invalid database engine: {config.engine}")
    return DATABASE_REGISTRY[config.engine](config)