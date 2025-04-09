from pydantic import BaseModel
from typing import List
from config.config import EmbeddingModelConfig

class EmbedderBase:
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self.provider = config.provider
    def load_model_from_provider(self):
        raise NotImplementedError
    def embed(self, text: List[str]):
        raise NotImplementedError
    def get_embedding_dimensions(self):
        raise NotImplementedError

class Embedder(EmbedderBase):
    def __init__(self, config: EmbeddingModelConfig):
        super().__init__(config)
        self.load_model_from_provider()
    def load_model_from_provider(self):
        # so far we only support sentence transformers
        if self.provider == "sf":
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.config.name)
            self.embedding_dimensions = self.model.get_sentence_embedding_dimension()
        else:
            raise ValueError(f"Provider {self.provider} not supported")

    def embed(self, text: List[str]):
        # if we support other providers, 
        # we need to add the logic here, most likely we need to add a provider specific class similar to how it is done for the database
        # but we can ignore for now
        return self.model.encode(text)
    def get_embedding_dimensions(self):
        return self.embedding_dimensions
