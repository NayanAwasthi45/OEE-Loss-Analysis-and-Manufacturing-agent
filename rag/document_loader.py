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

        allowed_folders = ["Rag_knowledge", "Domain_knowledge", "rag_knowledge", "domain_knowledge"]

        for root, dirs, files in os.walk(self.knowledge_dir):
            # Check if current path contains one of the allowed folders
            # We don't want to load from logs, reports, etc.
            path_parts = os.path.normpath(root).split(os.sep)
            is_allowed = any(folder in path_parts for folder in allowed_folders)
            
            if not is_allowed and root != self.knowledge_dir:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                category = os.path.basename(root)
                if category == os.path.basename(self.knowledge_dir):
                    category = "general"
                    
                if file.lower().endswith('.pdf'):
                    try:
                        extracted_pages = self._extract_pdf_text(file_path, file, category)
                        documents.extend(extracted_pages)
                        logger.info(f"Loaded {len(extracted_pages)} pages from {file}")
                    except Exception as e:
                        logger.error(f"Failed to load document {file}: {e}")
                elif file.lower().endswith('.json'):
                    try:
                        extracted_pages = self._extract_json_text(file_path, file, category)
                        documents.extend(extracted_pages)
                        logger.info(f"Loaded {len(extracted_pages)} items from {file}")
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

    def _extract_json_text(self, file_path: str, filename: str, category: str) -> List[Dict[str, Any]]:
        """Extracts text from a JSON file. Specifically handles manufacturing_playbook.json."""
        pages = []
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "error_codes" in data:
                # Handle structured error codes
                for i, err in enumerate(data["error_codes"]):
                    text = f"Error Code: {err.get('error_code')}\n"
                    text += f"Category: {err.get('category')}\n"
                    text += f"Description: {err.get('manufacturing_description')}\n"
                    text += f"OEE Impact: {err.get('expected_oee_behaviour')}\n"
                    text += f"Availability Impact: {err.get('expected_availability_impact')}\n"
                    text += f"Performance Impact: {err.get('expected_performance_impact')}\n"
                    text += f"Quality Impact: {err.get('expected_quality_impact')}\n"
                    
                    if "common_machine_symptoms" in err:
                        text += f"Symptoms: {', '.join(err['common_machine_symptoms'])}\n"
                    if "possible_mechanical_causes" in err:
                        text += f"Mechanical Causes: {', '.join(err['possible_mechanical_causes'])}\n"
                    if "common_maintenance_actions" in err:
                        text += f"Maintenance Actions: {', '.join(err['common_maintenance_actions'])}\n"
                        
                    pages.append({
                        "text": text.strip(),
                        "metadata": {
                            "source": filename,
                            "category": category,
                            "page_number": i + 1,
                            "error_code": err.get("error_code")
                        }
                    })
            else:
                # Generic JSON fallback
                pages.append({
                    "text": json.dumps(data, indent=2),
                    "metadata": {
                        "source": filename,
                        "category": category,
                        "page_number": 1
                    }
                })
        except Exception as e:
            logger.error(f"Error parsing JSON {filename}: {e}")
            
        return pages
