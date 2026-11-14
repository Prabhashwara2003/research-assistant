import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from langchain_core.documents import Document

from app.ai.pdf_extractor import PDFExtractor
from app.ai.text_chuncker import TextChunker
from app.ai.vector_store import VectorStoreManager

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
                records = json.loads(
                    chunk_path.read_text(
                        encoding="utf-8"
                    )
                )
                
                chunks = []
                
                for record in records:
                    chunks.append(
                        Document(
                            page_content=record["content"],
                            metadata = record["metadata"]
                        )
                    )
                    
            else:
                with TemporaryDirectory() as tempory_path:
                    result = self.extractor.extract(
                        pdf_path=pdf_path,
                        document_id=document_id,
                        output_directory=Path(tempory_path)
                    )
                    
                    chunks = self.chunker.split(
                        result.documents
                    )
                    
            if not chunks:
                raise ValueError(
                    "No chunks available to rebuild the index"
                )
            
            self.vector_store.index_document(
                document_id=document_id,
                chunks=chunks
            )