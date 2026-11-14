from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
   
   database_url : str = "sqlite:///./storage/research.db"
   
   anthropic_api_key : str =""
   claude_model : str =""
   
   langfuse_secret_key :str =""
   langfuse_public_key :str =""
   langfuse_base_url :str =""
   
   embedding_model : str="BAAI/bge-small-en-v1.5"
   
   max_pdf_size_mb :int =20
   
   upload_directory : str = "storage/uploads"
   extracted_directory : str = "storage/uploads/images"
   
   chunk_size : int = 1000
   chunk_overlap : int = 150
   retrieval_k : int= 5
   max_pdf_pages : int= 50
   
   chat_history_limit: int = 8
   max_images_per_answer: int = 2
   max_question_length: int = 2000
   
   enable_picture_description : bool = False
   picture_model : str = "HuggingFaceTB/SmolVLM-500M-Instruct"
   
   model_config = SettingsConfigDict(
       env_file = ".env",
       extra = "ignore"
   )
   
settings = Settings()

def get_upload_directory() -> Path:
    return Path(settings.upload_directory)