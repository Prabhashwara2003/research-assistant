import json
from pathlib import Path
from threading import Lock

from langchain_core.documents import Document

from app.ai.pdf_extractor import PDFExtractor
from app.ai.text_chuncker import TextChunker
from app.ai.vector_store import VectorStoreManager
from app.core.exceptions import DocumentIndexError

class IndexRecoveryService:
    def __init__(
        self,
        vector_store :VectorStoreManager,
        extractor : PDFExtractor,
        chunker : TextChunker,
        extracted_directory :Path
    ):
        self.vector_store = vector_store
        self.extractor = extractor
        self.chunker = chunker
        self.extracted_directory = extracted_directory
        
        self.lock = Lock()
    
    def ensure_index(
        self,
        document_id: str,
        pdf_path : Path
    )->None:
        if self.vector_store.has_document(document_id):
            return
        
        with self.lock:
            
            if self.vector_store.has_document(document_id):
                return
            
            chunk_path = (
                self.extracted_directory
                /document_id
                /"chunks.json"
            )
            
            if chunk_path.is_file():
                try:
                    records = json.loads(chunk_path.read_text(encoding="utf-8"))
                    if not isinstance(records, list):
                        raise ValueError("Chunk manifest must be a list")
                except (OSError, ValueError) as error:
                    raise DocumentIndexError("Invalid chunk manifest") from error
                
                chunks = []
                
                try:
                    for record in records:
                        if not isinstance(record["content"], str) or not isinstance(record["metadata"], dict):
                            raise ValueError("Invalid chunk record")
                        chunks.append(Document(page_content=record["content"], metadata=record["metadata"]))
                except (KeyError, TypeError, ValueError) as error:
                    raise DocumentIndexError("Invalid chunk manifest") from error
                    
            else:
                raise DocumentIndexError("Chunk manifest is missing; reprocessing is required")
                    
            if not chunks:
                raise DocumentIndexError(
                    "No chunks available to rebuild the index"
                )
            
            try:
                self.vector_store.index_document(document_id=document_id, chunks=chunks)
            except Exception as error:
                raise DocumentIndexError("Could not rebuild document index") from error
