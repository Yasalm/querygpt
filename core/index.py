from typing import List
from qdrant_client import QdrantClient
from config.config import IndexConfig

class Index:
    def __init__(self, config: IndexConfig):
        self.config = config
        self.index = None
        self.client = QdrantClient(url=config.url)
    
    def create(self):
        pass

    def add_items(self, items: List[str]):
        pass

    def query(self, query: str):
        pass
