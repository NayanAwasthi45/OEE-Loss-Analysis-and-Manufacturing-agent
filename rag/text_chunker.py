import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Splits document text into smaller, manageable chunks for embedding and vector search.
    Implements a simple character-based chunking strategy with overlap.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of document pages and splits their text into chunks.
        Preserves the original metadata and appends a chunk index.
        """
        logger.info(f"Chunking {len(documents)} document pages with size {self.chunk_size} and overlap {self.chunk_overlap}")
        chunked_docs = []

        for doc in documents:
            text = doc["text"]
            metadata = doc["metadata"]
            
            chunks = self._split_text(text)
            
            for i, chunk in enumerate(chunks):
                # Create a deep copy of metadata and add chunk info
                chunk_meta = metadata.copy()
                chunk_meta["chunk_index"] = i
                
                chunked_docs.append({
                    "text": chunk,
                    "metadata": chunk_meta
                })

        logger.info(f"Generated {len(chunked_docs)} total chunks.")
        return chunked_docs

    def _split_text(self, text: str) -> List[str]:
        """Splits a single string into overlapping chunks."""
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            
            # If we're not at the end of the text, try to find a nice breaking point (like a newline or period)
            if end < text_len:
                # Look back slightly to find a safe boundary
                boundary = text.rfind('\n', start, end)
                if boundary == -1 or boundary < start + (self.chunk_size // 2):
                    boundary = text.rfind('. ', start, end)
                    
                if boundary != -1 and boundary > start + (self.chunk_size // 2):
                    end = boundary + 1 # Include the period/newline
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            start = end - self.chunk_overlap

        return chunks
