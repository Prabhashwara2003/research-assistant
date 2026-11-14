import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from langchain_core.documents import Document

from app.core.database import Base
from app.models.document import Document as DatabaseDocument
from langchain_core.embeddings import Embeddings

from app.ai.index_recovery import IndexRecoveryService
from app.ai.vector_store import VectorStoreManager

from app.services.chat_service import ChatService

import app.models


class FakeRetriever:

    def retrieve(
        self,
        document_id,
        pdf_path,
        question
    ):
        return [
            Document(
                page_content=(
                    "The researchers used the CIFAR-10 "
                    "dataset for evaluation."
                ),
                metadata={
                    "document_id": document_id,
                    "page": 4,
                    "image_ids": []
                }
            )
        ]


class FakeAnswerGenerator:

    def prepare_search_query(
        self,
        question,
        history
    ):
        return question

    def generate_answer(
        self,
        question,
        history,
        retrieved_documents,
        images
    ):
        return (
            "The researchers used the CIFAR-10 "
            "dataset. [Page 4]"
        )


def test_chat_service(tmp_path):

    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}"
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    with TestingSession() as database:

        document = DatabaseDocument(
            id="paper-123",
            filename="research.pdf",
            file_path=str(tmp_path / "research.pdf"),
            status="completed"
        )

        database.add(document)
        database.commit()

        service = ChatService(
            database=database,
            retriever=FakeRetriever(),
            answer_generator=FakeAnswerGenerator(),
            history_limit=8,
            max_images=2
        )

        response = service.ask_question(
            document_id="paper-123",
            question="What dataset was used?"
        )

        assert "CIFAR-10" in response.answer
        assert response.sources[0].page == 4

        history = service.get_chat_history(
            document_id="paper-123"
        )

        assert len(history) == 2

        assert history[0].role == "user"
        assert history[1].role == "assistant"

        assert history[0].content == (
            "What dataset was used?"
        )

    engine.dispose()
    
class FakeEmbeddings(Embeddings):

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        text = text.lower()

        return [
            float(text.count("dataset")),
            float(text.count("accuracy")),
            1.0
        ]


def test_index_recovery(tmp_path):

    document_id = "paper-123"

    extracted_directory = tmp_path / "extracted"
    document_directory = (
        extracted_directory / document_id
    )

    document_directory.mkdir(parents=True)

    chunks = [
        {
            "content": "The dataset contains 500 images.",
            "metadata": {
                "document_id": document_id,
                "page": 3,
                "image_ids": []
            }
        }
    ]

    chunks_path = document_directory / "chunks.json"

    chunks_path.write_text(
        json.dumps(chunks),
        encoding="utf-8"
    )

    manager = VectorStoreManager(
        embeddings=FakeEmbeddings()
    )

    assert not manager.has_document(document_id)

    recovery = IndexRecoveryService(
        vector_store=manager,
        extractor=None,
        chunker=None,
        extracted_directory=extracted_directory
    )

    recovery.ensure_index(
        document_id=document_id,
        pdf_path=tmp_path / "paper.pdf"
    )

    assert manager.has_document(document_id)

    results = manager.search(
        document_id=document_id,
        question="What dataset was used?",
        k=1
    )

    assert len(results) == 1
    assert results[0].metadata["page"] == 3
