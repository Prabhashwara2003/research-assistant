from contextlib import contextmanager
from threading import Lock


class ChatLockManager:
    """Serializes exchanges per document within one application process."""

    def __init__(self):
        self._guard = Lock()
        self._locks: dict[str, Lock] = {}

    @contextmanager
    def acquire(self, document_id: str):
        with self._guard:
            document_lock = self._locks.setdefault(document_id, Lock())
        with document_lock:
            yield
