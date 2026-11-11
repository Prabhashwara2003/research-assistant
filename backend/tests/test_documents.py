
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_upload_directory
from app.core.database import Base, get_db
from app.routers.document_router import router as document_router

import app.models


@pytest.fixture
def client(tmp_path):

    # Create a temporary SQLite database.
    database_path = tmp_path / "test.db"

    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False
    )

    # Replace the production database dependency.
    def override_get_db():
        database = TestingSession()

        try:
            yield database
        finally:
            database.close()

    # Replace the production upload directory.
    def override_upload_directory():
        return tmp_path / "uploads"

    test_app = FastAPI()
    test_app.include_router(document_router)

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[
        get_upload_directory
    ] = override_upload_directory

    with TestClient(test_app) as test_client:
        yield test_client

    test_engine.dispose()


def test_upload_pdf(client):

    # Minimal bytes for testing the upload flow.
    # This is not a complete readable research paper.
    pdf_content = b"%PDF-1.4\nTest document"

    response = client.post(
        "/api/documents",
        files={
            "file": (
                "research.pdf",
                pdf_content,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 201

    document = response.json()

    assert document["filename"] == "research.pdf"
    assert document["status"] == "pending"
    assert document["id"] is not None


def test_reject_non_pdf(client):

    response = client.post(
        "/api/documents",
        files={
            "file": (
                "notes.txt",
                b"Hello world",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


def test_reject_invalid_pdf_content(client):

    response = client.post(
        "/api/documents",
        files={
            "file": (
                "fake.pdf",
                b"This is not a PDF",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400


def test_get_document(client):

    upload_response = client.post(
        "/api/documents",
        files={
            "file": (
                "paper.pdf",
                b"%PDF-1.4\nTest document",
                "application/pdf"
            )
        }
    )

    document_id = upload_response.json()["id"]

    response = client.get(
        f"/api/documents/{document_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == document_id


def test_get_missing_document(client):

    response = client.get(
        "/api/documents/nonexistent"
    )

    assert response.status_code == 404


def test_get_original_pdf(client):

    pdf_content = b"%PDF-1.4\nTest document"

    upload_response = client.post(
        "/api/documents",
        files={
            "file": (
                "paper.pdf",
                pdf_content,
                "application/pdf"
            )
        }
    )

    document_id = upload_response.json()["id"]

    response = client.get(
        f"/api/documents/{document_id}/file"
    )

    assert response.status_code == 200
    assert response.content == pdf_content
    assert response.headers["content-type"] == "application/pdf"
