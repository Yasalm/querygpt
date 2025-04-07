from config.config import SourceConfig

def load_sources(config: List[SourceConfig]):
    return [init_database_from_config(source.database) for source in config]

class Sources:
    def __init__(self, config: List[SourceConfig]):
        self.sources = load_sources(config)

    def __getitem__(self, index: int):
        return self.sources[index]