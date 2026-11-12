from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from app.ai.pdf_extractor import DoclingPDFExtractor
from app.ai.text_chuncker import TextChunker
from app.ai.embedding_provider import EmbeddingProvider
from app.ai.vector_store import VectorStoreManager

from app.services.document_processing_service import (
    
    DocumentProcessingService
) 

@lru_cache
def get_extractor()->DoclingPDFExtractor:
    return DoclingPDFExtractor(
        max_pages=settings.max_pdf_pages,
        enable_description=settings.enable_picture_description,
        picture_model=settings.picture_model
    )
    
@lru_cache
def get_vector_store_manager()->VectorStoreManager:
    provider = EmbeddingProvider(
        model_name=settings.embedding_model
    )
    
    embeddings = provider.create()
    
    return VectorStoreManager(embeddings)

def get_documents_processor(
    database : Session = Depends(get_db)
)->DocumentProcessingService:
    
    return DocumentProcessingService(
        database=database,
        extractor=get_extractor(),
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        ),
        vector_store=get_vector_store_manager(),
        extracted_directory=Path(
            settings.extracted_directory
        )
    )
