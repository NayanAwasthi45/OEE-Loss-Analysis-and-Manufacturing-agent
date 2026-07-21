import logging
from typing import List, Dict, Any
from .embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class Retriever:
    """
    High-level orchestration for executing semantic searches.
    Coordinates the EmbeddingService to embed the user query, and the
    VectorStore to fetch the relevant context.
    """

    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant chunks for a given query.
        """
        logger.info(f"Retrieving top {top_k} documents for query: '{query}'")
        
        # 1. Embed the query
        query_embedding = self.embedding_service.embed_query(query)
        
        # 2. Search ChromaDB
        results = self.vector_store.search(query_embedding, n_results=top_k)
        
        logger.info(f"Retrieved {len(results)} relevant chunks.")
        return results
