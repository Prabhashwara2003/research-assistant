from pathlib import Path
import logging

from sqlalchemy.orm import Session

from app.ai.answer_generator import AnswerGenerator
from app.ai.rag_retriever import RAGRetriever
from app.core.observability import Observability
from app.core.chat_locks import ChatLockManager
from app.core.exceptions import (AnswerGenerationError, DocumentIndexError,
                                 DocumentNotFoundError, DocumentNotReadyError)
from app.repositories.document_repository import DocumentRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat_schema import ChatResponse, SourceReference

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(
        self,
        database: Session,
        retriever: RAGRetriever,
        answer_generator: AnswerGenerator,
        history_limit: int,
        max_images: int,
        observability: Observability | None = None,
        chat_locks: ChatLockManager | None = None,
    ):
        self.database = database
        self.retriever = retriever
        self.answer_generator = answer_generator
        self.history_limit = history_limit
        self.max_images = max_images
        self.observability = observability or Observability()
        self.chat_locks = chat_locks or ChatLockManager()
        self.document_repository = DocumentRepository(database)
        self.image_repository = ImageRepository(database)
        self.message_repository = MessageRepository(database)

    def ask_question(
        self,
        document_id: str,
        question: str,
    ) -> ChatResponse:
        with self.chat_locks.acquire(document_id):
            with self.observability.trace(
                "research-chat", metadata={"document_id": document_id}
            ):
                return self._answer_question(document_id, question)

    def _answer_question(
        self,
        document_id: str,
        question: str,
    ) -> ChatResponse:
        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found")

        if document.status not in ("indexed", "completed"):
            raise DocumentNotReadyError("Document is not ready for questions")

        history = self.message_repository.get_recent_messages(
            document_id=document_id,
            limit=self.history_limit,
        )

        with self.observability.trace("prepare-search-query"):
            try:
                search_query = self.answer_generator.prepare_search_query(
                    question=question, history=history,
                )
            except Exception as error:
                logger.exception("Search query rewrite failed for %s", document_id)
                raise AnswerGenerationError("Search query rewrite failed") from error

        with self.observability.trace(
            "retrieve-document-evidence",
            metadata={
                "document_id": document_id,
                "retrieval_k": getattr(self.retriever, "retrieval_k", None)
            }
        ):
            try:
                retrieved_documents = self.retriever.retrieve(
                    document_id=document_id,
                    pdf_path=Path(document.file_path),
                    question=search_query
                )
            except Exception as error:
                logger.exception("Document retrieval failed for %s", document_id)
                raise DocumentIndexError("Document retrieval failed") from error

        relevant_images = []
        seen_image_ids = set()

        for chunk in retrieved_documents:
            image_ids = chunk.metadata.get("image_ids", [])

            for image_id in image_ids:
                if image_id in seen_image_ids:
                    continue

                seen_image_ids.add(image_id)

                image = self.image_repository.find_by_id(
                    document_id=document_id,
                    image_id=image_id,
                )

                if image is None:
                    continue

                if image.decorative_candidate:
                    continue

                image_path = Path(image.file_path)

                if not image_path.is_file():
                    continue

                if image_path.stat().st_size > 5 * 1024 * 1024:
                    continue

                relevant_images.append(image)

                if len(relevant_images) >= self.max_images:
                    break

            if len(relevant_images) >= self.max_images:
                break

        with self.observability.trace(
            "generate-grounded-answer",
            metadata={
                "document_id": document_id,
                "retrieved_chunks": len(retrieved_documents),
                "selected_images": len(relevant_images)
            }
        ):
            try:
                generated_answer = self.answer_generator.generate_answer(
                    question=question, history=history,
                    retrieved_documents=retrieved_documents, images=relevant_images
                )
            except Exception as error:
                logger.exception("Answer generation failed for %s", document_id)
                raise AnswerGenerationError("Answer generation failed") from error

        if not generated_answer.text.strip():
            raise AnswerGenerationError("The model returned an empty answer")

        assistant_message = self.message_repository.save_exchange(
            document_id=document_id,
            question=question,
            answer=generated_answer.text,
        )

        source_reference = []
        seen_source = set()

        attached_image_ids = set(generated_answer.attached_image_ids)

        for chunk in retrieved_documents:
            page_number = chunk.metadata.get("page")

            if page_number is None:
                continue

            image_ids = chunk.metadata.get("image_ids", [])
            image_id = None

            for candidate_id in image_ids:
                if candidate_id in attached_image_ids:
                    image_id = candidate_id
                    break

            source_key = (page_number, image_id)

            if source_key in seen_source:
                continue

            seen_source.add(source_key)
            source_reference.append(
                SourceReference(
                    page=page_number,
                    image_id=image_id,
                )
            )

        return ChatResponse(
            message_id=assistant_message.id,
            answer=generated_answer.text,
            sources=source_reference,
        )

    def get_chat_history(self, document_id: str):
        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found")

        return self.message_repository.get_all_messages(document_id)
