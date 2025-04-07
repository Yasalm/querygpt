from pydantic import BaseModel
from typing import List
from config.config import EmbeddingModelConfig



class Embedder:
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config

    def embed(self, text: str):
        pass

    def embed_batch(self, texts: List[str]):
        pass