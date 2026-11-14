import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.ai.answer_generator import AnswerGenerator
from app.ai.index_recovery import IndexRecoveryService
from app.ai.vector_store import VectorStoreManager
from app.core.chat_locks import ChatLockManager
from app.core.exceptions import DocumentIndexError
from app.core.observability import Observability
from app.main import app


def test_disabled_observability_needs_no_credentials():
    tracing = Observability()
    with tracing.trace("test"):
        assert tracing.get_callbacks() == []
    tracing.shutdown()


def test_enabled_observability_requires_credentials():
    with pytest.raises(ValueError, match="keys are required"):
        Observability(enabled=True)


def test_enabled_observability_uses_injected_credentials(monkeypatch):
    import langfuse

    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(langfuse, "Langfuse", FakeClient)
    tracing = Observability(enabled=True, public_key="test-public",
                            secret_key="test-secret", base_url="https://example.test")
    assert calls[0]["public_key"] == "test-public"
    assert calls[0]["base_url"] == "https://example.test"
    tracing.shutdown()
    assert calls[-1] == "shutdown"


def test_error_handlers():
    from app.core.exceptions import (DocumentNotFoundError, DocumentNotReadyError,
                                     AnswerGenerationError)

    errors = [
        (DocumentNotFoundError(), 404),
        (DocumentNotReadyError(), 409),
        (DocumentIndexError(), 503),
        (AnswerGenerationError(), 502),
    ]
    with TestClient(app) as client:
        for error, status in errors:
            def raise_error():
                raise error
            app.add_api_route("/phase4c-error", raise_error)
            response = client.get("/phase4c-error")
            assert response.status_code == status
            app.router.routes.pop()
    def unexpected_error():
        raise RuntimeError("internal detail")
    app.add_api_route("/phase4c-unexpected", unexpected_error)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/phase4c-unexpected")
        assert response.status_code == 500
        assert "internal detail" not in response.text
    finally:
        app.router.routes.pop()


def test_chat_locks_serialize_and_release():
    manager = ChatLockManager()
    entered = Event()
    release = Event()
    second_entered = Event()

    def first():
        with manager.acquire("paper"):
            entered.set()
            assert release.wait(5)

    def second():
        assert entered.wait(5)
        with manager.acquire("paper"):
            second_entered.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_task = pool.submit(first)
        second_task = pool.submit(second)
        assert entered.wait(5)
        assert not second_entered.is_set()
        release.set()
        first_task.result()
        second_task.result()
    assert second_entered.is_set()
    with manager.acquire("paper"):
        with manager.acquire("other-paper"):
            pass
    with pytest.raises(RuntimeError):
        with manager.acquire("paper"):
            raise RuntimeError()
    with manager.acquire("paper"):
        pass


def test_answer_reports_only_attached_images(tmp_path):
    class FakeModel:
        def invoke(self, messages, config=None):
            return SimpleNamespace(content="Answer [Page 1]")

    valid = tmp_path / "valid.png"
    valid.write_bytes(b"image")
    large = tmp_path / "large.png"
    large.write_bytes(b"x" * (5 * 1024 * 1024 + 1))
    images = [SimpleNamespace(image_id=name, file_path=str(path), page_number=1)
              for name, path in [("valid", valid), ("missing", tmp_path / "missing.png"),
                                 ("large", large)]]
    answer = AnswerGenerator(FakeModel()).generate_answer(
        "Question", [], [Document(page_content="Evidence", metadata={"page": 1})], images
    )
    assert answer.text == "Answer [Page 1]"
    assert answer.attached_image_ids == ["valid"]


def test_invalid_and_missing_manifest_do_not_publish_index(tmp_path):
    class FakeStore:
        def has_document(self, document_id):
            return False
        def index_document(self, document_id, chunks):
            pytest.fail("Index must not be published")

    recovery = IndexRecoveryService(FakeStore(), None, None, tmp_path)
    with pytest.raises(DocumentIndexError, match="missing"):
        recovery.ensure_index("paper", tmp_path / "paper.pdf")
    directory = tmp_path / "paper"
    directory.mkdir()
    (directory / "chunks.json").write_text(json.dumps({"bad": "manifest"}))
    with pytest.raises(DocumentIndexError, match="Invalid"):
        recovery.ensure_index("paper", tmp_path / "paper.pdf")


def test_failed_embedding_does_not_publish_index():
    from langchain_core.embeddings import Embeddings

    class FailingEmbeddings(Embeddings):
        def embed_documents(self, texts):
            raise RuntimeError("embedding failed")

        def embed_query(self, text):
            raise RuntimeError("embedding failed")

    store = VectorStoreManager(FailingEmbeddings())
    with pytest.raises(RuntimeError, match="embedding failed"):
        store.index_document(document_id="paper", chunks=[Document(page_content="text")])
    assert not store.has_document("paper")
