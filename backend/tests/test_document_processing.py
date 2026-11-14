
from pathlib import Path

import pytest
from PIL import Image

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.database import Base
from app.models.document import Document as DatabaseDocument
from app.models.document_image import DocumentImage

from app.ai.extraction_model import (
    ExtractedImage,
    ExtractionResult
)
from app.ai.text_chuncker import TextChunker
from app.ai.vector_store import VectorStoreManager

from app.services.document_processing_service import (
    DocumentProcessingService
)

import app.models


class FakeExtractor:

    def extract(
        self,
        pdf_path: Path,
        document_id: str,
        output_directory: Path
    ) -> ExtractionResult:

        image_id = f"{document_id}_p2_img1"

        image_directory = output_directory / "images"
        image_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        image_path = image_directory / f"{image_id}.png"

        image = Image.new(
            "RGB",
            (100, 100),
            "white"
        )

        image.save(image_path)

        markdown = (
            "# Research Paper\n\n"
            "The model achieved high accuracy.\n\n"
            f"[IMAGE: {image_id}]\n"
            "Caption: Model accuracy comparison\n"
            "[/IMAGE]"
        )

        documents = [
            Document(
                page_content=(
                    "The model achieved high accuracy."
                ),
                metadata={
                    "document_id": document_id,
                    "page": 1,
                    "image_ids": [],
                    "content_type": "text"
                }
            ),
            Document(
                page_content=(
                    f"[IMAGE: {image_id}]\n"
                    "Caption: Model accuracy comparison\n"
                    "[/IMAGE]"
                ),
                metadata={
                    "document_id": document_id,
                    "page": 2,
                    "image_ids": [image_id],
                    "content_type": "image"
                }
            )
        ]

        images = [
            ExtractedImage(
                image_id=image_id,
                document_id=document_id,
                page_number=2,
                file_path=image_path,
                caption="Model accuracy comparison"
            )
        ]

        return ExtractionResult(
            markdown=markdown,
            documents=documents,
            images=images
        )


class FakeEmbeddings(Embeddings):

    def embed_documents(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        return [
            self.embed_query(text)
            for text in texts
        ]

    def embed_query(
        self,
        text: str
    ) -> list[float]:

        text = text.lower()

        return [
            float(text.count("model")),
            float(text.count("accuracy")),
            float(text.count("comparison"))
        ]


@pytest.mark.parametrize("failure_stage", ["extraction", "embedding"])
def test_processing_failure_preserves_document_and_cleans_temporary_files(
    tmp_path, failure_stage
):
    engine = create_engine(f"sqlite:///{tmp_path / 'failure.db'}")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest")

    class FailingExtractor:
        def extract(self, pdf_path, document_id, output_directory):
            (output_directory / "temporary.txt").write_text("partial")
            raise RuntimeError("extraction failed")

    class FailingEmbeddings(FakeEmbeddings):
        def embed_documents(self, texts):
            raise RuntimeError("embedding failed")

    with TestingSession() as database:
        document = DatabaseDocument(id="paper", filename="paper.pdf",
                                    file_path=str(pdf_path), status="pending")
        database.add(document)
        database.commit()
        store = VectorStoreManager(FailingEmbeddings() if failure_stage == "embedding"
                                   else FakeEmbeddings())
        processor = DocumentProcessingService(
            database=database,
            extractor=FailingExtractor() if failure_stage == "extraction" else FakeExtractor(),
            chunker=TextChunker(chunk_size=200, chunk_overlap=30),
            vector_store=store,
            extracted_directory=tmp_path / "extracted"
        )
        with pytest.raises(RuntimeError, match="failed"):
            processor.process("paper")
        database.refresh(document)
        assert document.status == "failed"
        assert pdf_path.is_file()
        assert not store.has_document("paper")
        assert list((tmp_path / "extracted").iterdir()) == []
    engine.dispose()


def test_processing_database_failure_removes_new_output(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'commit.db'}")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest")

    with TestingSession() as database:
        document = DatabaseDocument(id="paper", filename="paper.pdf",
                                    file_path=str(pdf_path), status="pending")
        database.add(document)
        database.commit()
        original_commit = database.commit
        commit_count = 0

        def fail_final_commit():
            nonlocal commit_count
            commit_count += 1
            if commit_count == 2:
                raise RuntimeError("database commit failed")
            original_commit()

        monkeypatch.setattr(database, "commit", fail_final_commit)
        store = VectorStoreManager(FakeEmbeddings())
        processor = DocumentProcessingService(
            database=database, extractor=FakeExtractor(),
            chunker=TextChunker(chunk_size=200, chunk_overlap=30),
            vector_store=store, extracted_directory=tmp_path / "extracted"
        )
        with pytest.raises(RuntimeError, match="database commit failed"):
            processor.process("paper")
        database.refresh(document)
        assert document.status == "failed"
        assert pdf_path.is_file()
        assert not (tmp_path / "extracted" / "paper").exists()
        assert not store.has_document("paper")
    engine.dispose()


def test_document_processing(tmp_path):

    database_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    pdf_path = tmp_path / "research.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest")

    with TestingSession() as database:

        document = DatabaseDocument(
            id="test-paper",
            filename="research.pdf",
            file_path=str(pdf_path),
            status="pending"
        )

        database.add(document)
        database.commit()

        vector_store = VectorStoreManager(
            embeddings=FakeEmbeddings()
        )

        processor = DocumentProcessingService(
            database=database,
            extractor=FakeExtractor(),
            chunker=TextChunker(
                chunk_size=200,
                chunk_overlap=30
            ),
            vector_store=vector_store,
            extracted_directory=tmp_path / "extracted"
        )

        chunk_count = processor.process(
            document_id="test-paper"
        )

        assert chunk_count == 2

        database.refresh(document)

        assert document.status == "indexed"

        # The image metadata should exist in SQLite.
        saved_image = database.get(
            DocumentImage,
            "test-paper_p2_img1"
        )

        assert saved_image is not None
        assert saved_image.page_number == 2

        # The actual PNG should exist on disk.
        assert Path(saved_image.file_path).is_file()

        # The Markdown should contain the same ID.
        markdown_path = (
            tmp_path
            / "extracted"
            / "test-paper"
            / "document.md"
        )

        markdown = markdown_path.read_text(
            encoding="utf-8"
        )

        assert "[IMAGE: test-paper_p2_img1]" in markdown

        # The in-memory index should be available.
        assert vector_store.has_document("test-paper")

        results = vector_store.search(
            document_id="test-paper",
            question="Model accuracy comparison",
            k=2
        )

        assert len(results) == 2

        # A failed retry must leave the previous extraction intact.
        document.status = "failed"
        database.commit()

        with pytest.raises(ValueError, match="output already exists"):
            processor.process(document_id="test-paper")

        assert Path(saved_image.file_path).is_file()
        assert markdown_path.is_file()

    engine.dispose()
