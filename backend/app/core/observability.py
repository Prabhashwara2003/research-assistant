"""Optional Langfuse tracing shared by the backend."""

from contextlib import nullcontext
import logging

logger = logging.getLogger(__name__)

SAFE_FIELDS = {
    "document_id", "content_block_count", "image_count", "chunk_count",
    "retrieval_k", "retrieved_chunks", "selected_images", "attached_images",
    "model", "model_name", "input_tokens", "output_tokens",
}


def _mask_payload(data):
    """Keep operational counts while excluding prompts, documents and image data."""
    if isinstance(data, dict):
        safe = {key: value for key, value in data.items()
                if key in SAFE_FIELDS and isinstance(value, (str, int, float, bool))}
        return safe if safe else "[redacted]"
    return "[redacted]"


class Observability:
    def __init__(self, enabled: bool = False, public_key: str = "",
                 secret_key: str = "", base_url: str = "https://cloud.langfuse.com"):
        self.client = None
        self.enabled = enabled
        if enabled:
            if not public_key or not secret_key:
                raise ValueError("Langfuse public and secret keys are required when enabled")
            from langfuse import Langfuse
            self.client = Langfuse(public_key=public_key, secret_key=secret_key,
                                   base_url=base_url, mask=_mask_payload)
            self.public_key = public_key

    def get_callbacks(self) -> list:
        if self.client is None:
            return []
        from langfuse.langchain import CallbackHandler
        return [CallbackHandler(public_key=self.public_key)]

    def trace(self, name: str, metadata: dict | None = None):
        if self.client is None:
            return nullcontext()
        try:
            return self.client.start_as_current_observation(
                name=name, as_type="span", metadata=metadata
            )
        except Exception:
            logger.exception("Could not start Langfuse observation %s", name)
            return nullcontext()

    def shutdown(self) -> None:
        if self.client is not None:
            try:
                self.client.shutdown()
            except Exception:
                logger.exception("Could not shut down Langfuse")
