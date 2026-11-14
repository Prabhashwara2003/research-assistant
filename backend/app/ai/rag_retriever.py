from pathlib import Path

from langchain_core.documents import Document

from app.ai.index_recovery import IndexRecoveryService

from app.ai.vector_store import VectorStoreManager

class RAGRetriever:
    def __init__(
        self,
        vector_store : VectorStoreManager,
        index_recovery: IndexRecoveryService,
        retrieval_k : int
    ):
        self.vector_store = vector_store
        self.index_recovery = index_recovery
        self.retrieval_k = retrieval_k
    
    def retrieve(
        self,
        document_id : str,
        pdf_path : Path,
        question : str
    )->list[Document]:
        
        self.index_recovery.ensure_index(
            document_id=document_id,
            pdf_path=pdf_path
        )
        
        documents = self.vector_store.search(
            document_id=document_id,
            question=question,
            k = self.retrieval_k
        )
        
        return documents
