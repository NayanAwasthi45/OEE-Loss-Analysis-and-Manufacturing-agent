import os
import logging
import threading
import uuid
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages the ChromaDB instance for storing and retrieving document embeddings.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(VectorStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "data/chroma_db", collection_name: str = "manufacturing_knowledge"):
        if getattr(self, '_initialized', False):
            return
            
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at {self.db_path} with collection {self.collection_name}")
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"} # Use cosine similarity
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
            
        self._initialized = True

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Adds text chunks and their embeddings to ChromaDB.
        """
        if not chunks or not embeddings or len(chunks) != len(embeddings):
            logger.error("Invalid chunks or embeddings provided to VectorStore.")
            return

        logger.info(f"Adding {len(chunks)} documents to ChromaDB collection: {self.collection_name}")
        
        ids = []
        texts = []
        metadatas = []
        
        for chunk in chunks:
            # Generate a unique ID for each chunk
            ids.append(str(uuid.uuid4()))
            texts.append(chunk["text"])
            
            # Chroma metadata values must be strings, ints, or floats
            safe_meta = {}
            for k, v in chunk["metadata"].items():
                if isinstance(v, (str, int, float, bool)):
                    safe_meta[k] = v
                else:
                    safe_meta[k] = str(v)
            metadatas.append(safe_meta)
            
        try:
            # Add in batches to avoid overwhelming the SQLite backend of Chroma
            batch_size = 5000
            for i in range(0, len(ids), batch_size):
                self.collection.add(
                    ids=ids[i:i+batch_size],
                    embeddings=embeddings[i:i+batch_size],
                    documents=texts[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )
            logger.info("Successfully added documents to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise

    def search(self, query_embedding: List[float], n_results: int = 4) -> List[Dict[str, Any]]:
        """
        Searches ChromaDB for the closest documents to the query embedding.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            return []

    def get_collection_count(self) -> int:
        """Returns the total number of documents in the collection."""
        try:
            return self.collection.count()
        except Exception:
            return 0
