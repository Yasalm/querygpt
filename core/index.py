from typing import List
from qdrant_client import QdrantClient
from config.config import IndexConfig
from core.embeders import Embedder
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class Index:
    def __init__(self, config: IndexConfig):
        self.config = config
        self.index = config.name
        self.client = QdrantClient(url=config.url)
        self.__post_init__()

    def __post_init__(self):
        try: 
            self.client.get_collection(self.index)
        except Exception as e:
            self.create()
        self.embedder = Embedder(self.config.embedding_model)

    def create(self, index: str = None):
        index = index or self.index
        self.client.create_collection(
            collection_name=index,
            vectors_config=VectorParams(
                size=self.config.embedding_model.dimensions,
                distance=Distance.COSINE # should be configurable :( 
            )
        )
    def upsert(self, embeddings: List[List[float]], payloads: List[dict],):
        self.client.upsert(
            collection_name=self.index,
            points=[PointStruct(id=id, vector=embedding, payload=payload) for id, embedding, payload in zip(range(len(embeddings)), embeddings, payloads)]
        )
    def retrieve(self, query: str, index: str = None,top_k: int = 10):
        index = index or self.index
        if not isinstance(query, list):
            query = [query]
        query_vector = self.embedder.embed(query)[0].tolist() if hasattr(self.embedder.embed(query)[0], 'tolist') else self.embedder.embed(query)[0]
    
        if isinstance(query_vector[0], list):
            query_vector = query_vector[0]
        hits = self.client.search(
            collection_name=index,
            query_vector=query_vector,
            limit=top_k
        )
        results = []
        for hit in hits:
            metadata = {
                "score": hit.score,
                "metadata": hit.payload,
            }
            results.append(metadata)
        return results
