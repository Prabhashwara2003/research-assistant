from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
   
   database_url : str = "sqlite:///./storage/research.db"
   
   anthropic_value : str =""
   claude_model : str =""
   
   langfuse_secret_key :str =""
   langfuse_public_key :str =""
   langfuse_base_url :str =""
   
   embedding_model : str="BAAI/bge-small-en-v1.5"
   
   max_pdf_size_mb :int =20
   
   upload_directory : str = "storage/uploads"
   
   model_config = SettingsConfigDict(
       env_file = ".env",
       extra = "ignore"
   )
   
  
       
   
settings = Settings()

def get_upload_path() -> Path:
    return Path(settings.upload_directory)