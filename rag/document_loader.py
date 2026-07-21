import os
import logging
from typing import List, Dict, Any
import PyPDF2

logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    Loads manufacturing documents (PDFs) from the rag_knowledge directory.
    Extracts text and metadata (filename, category/folder, page number) for ChromaDB ingestion.
    """

    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = knowledge_dir

    def load_all_documents(self) -> List[Dict[str, Any]]:
        """
        Recursively scans the knowledge directory for PDF files,
        extracts their text page by page, and attaches metadata.
        """
        logger.info(f"Scanning for documents in: {self.knowledge_dir}")
        documents = []

        if not os.path.exists(self.knowledge_dir):
            logger.warning(f"RAG knowledge directory not found: {self.knowledge_dir}")
            return documents

        for root, dirs, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    # Category is the folder name containing the PDF
                    category = os.path.basename(root)
                    if category == os.path.basename(self.knowledge_dir):
                        category = "general"

                    try:
                        extracted_pages = self._extract_pdf_text(file_path, file, category)
                        documents.extend(extracted_pages)
                        logger.info(f"Loaded {len(extracted_pages)} pages from {file}")
                    except Exception as e:
                        logger.error(f"Failed to load document {file}: {e}")

        logger.info(f"Successfully loaded a total of {len(documents)} pages from all documents.")
        return documents

    def _extract_pdf_text(self, file_path: str, filename: str, category: str) -> List[Dict[str, Any]]:
        """Extracts text from a single PDF file, page by page."""
        pages = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "text": text.strip(),
                        "metadata": {
                            "source": filename,
                            "category": category,
                            "page_number": i + 1,
                        }
                    })
        return pages
