from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingProvider:
    
    def __init__(self,model_name : str):
        self.model_name = model_name
        
    def create(self)->Embeddings:
        embeddings = HuggingFaceEmbeddings(
            model_name = self.model_name,
            encode_kwargs={
                "normalize_embedding" : True
            }
        )
        
        return embeddings