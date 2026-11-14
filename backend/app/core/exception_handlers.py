import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (AnswerGenerationError, DocumentIndexError,
                                 DocumentNotFoundError, DocumentNotReadyError)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    mappings = {
        DocumentNotFoundError: (404, "Document not found"),
        DocumentNotReadyError: (409, "Document is not ready"),
        DocumentIndexError: (503, "Document index is unavailable"),
        AnswerGenerationError: (502, "Answer generation failed"),
    }
    for error_type, (status_code, detail) in mappings.items():
        async def handler(request: Request, error: Exception,
                          code=status_code, message=detail):
            logger.warning("%s: %s", type(error).__name__, error)
            return JSONResponse(status_code=code, content={"detail": message})
        app.add_exception_handler(error_type, handler)
