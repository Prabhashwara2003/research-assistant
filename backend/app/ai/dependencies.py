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

from langchain_core.language_models import BaseChatModel
from app.ai.llm_provider import LLMProvider
from app.ai.summary_generator import SummaryGenerator
from app.services.summary_service import SummaryService

from app.ai.index_recovery import IndexRecoveryService
from app.ai.rag_retriever import RAGRetriever
from app.ai.answer_generator import AnswerGenerator

from app.services.chat_service import ChatService

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

@lru_cache
def get_chat_model()->BaseChatModel:
    
    if not settings.anthropic_api_key:
        raise ValueError(
            "Anthropic key is not configured"
        )
    if not settings.claude_model:
        raise ValueError(
            "Claude model isnot configured"
        )
        
    provider = LLMProvider(
        api_key=settings.anthropic_api_key,
        model_name=settings.claude_model
    )
    
    return provider.create_model()

def get_Summary_service(
        database : Session = Depends(get_db)
    )->SummaryService:
        generator = SummaryGenerator(
            model = get_chat_model()
        )
        
        return SummaryService(
            database=database,
            summary_generator=generator,
            extracted_directory=Path(settings.extracted_directory)
        )
    
@lru_cache
def get_index_recovery()-> IndexRecoveryService:
    
    return IndexRecoveryService(
        vector_store=get_vector_store_manager(),
        extractor=get_extractor(),
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        ),
        extracted_directory=Path(
            settings.extracted_directory
        )
    )

def get_chat_service(
    database : Session = Depends(get_db)
)->ChatService:
    retriever = RAGRetriever(
        vector_store = get_vector_store_manager(),
        index_recovery = get_index_recovery(),
        retrieval_k = settings.retrieval_k
    )
    
    answer_generator = AnswerGenerator(
        model=get_chat_model()
    )

    return ChatService(
        database=database,
        retriever=retriever,
        answer_generator=answer_generator,
        history_limit=settings.chat_history_limit,
        max_images=settings.max_images_per_answer
    )
