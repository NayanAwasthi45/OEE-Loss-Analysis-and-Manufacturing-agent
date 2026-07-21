import logging
import threading
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Generates vector embeddings for text chunks using a local SentenceTransformer model.
    Using a local model avoids API costs for embedding massive PDF documents.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(EmbeddingService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if getattr(self, '_initialized', False):
            return
            
        logger.info(f"Initializing EmbeddingService with model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {model_name}: {e}")
            raise
        self._initialized = True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Takes a list of strings and returns a list of embedding vectors.
        """
        if not texts:
            return []
            
        logger.debug(f"Embedding {len(texts)} chunks...")
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            # ChromaDB expects lists of floats
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a single user query for semantic search.
        """
        try:
            embedding = self.model.encode(query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
