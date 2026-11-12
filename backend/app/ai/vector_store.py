from threading import Lock

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.embeddings import Embeddings 
from langchain_core.documents import Document

class VectorStoreManager:
    
    def __init__(
        self,
        embeddings : Embeddings,
    ):
        self.embeddings = embeddings
        self.store : dict[str,InMemoryVectorStore] = {}
        self.lock = Lock()
        
    def has_document(self,document_id : str)->bool:
        with self.lock:
            return document_id in self.store
    
    def index_document(
        self,
        chunks : list[Document],
        document_id : str
    )->None:
        if not chunks:
            raise ValueError(
                "Cannot index an empty documents"
            )
        new_store = InMemoryVectorStore(
            embedding=self.embeddings
        )
        
        new_store.add_documents(chunks)
        
        with self.lock:
            self.store[document_id] = new_store
    
    def search (
        self,
        document_id : str,
        question : str,
        k : int = 5
    )-> list[Document]:
        with self.lock:
            store = self.store.get(document_id)
        
            if store is None:
                raise ValueError(
                    "Document index is not available"
                )
                
        return store.similarity_search(
            query=question,
            k=k
        )
    
    def remove_document(
        self,
        document_id : str
        ) -> None:
        with self.lock :
            self.store.pop(document_id,None)
    
