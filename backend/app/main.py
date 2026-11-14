from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base,engine
from app.routers import document_router,chat_router
from app.ai.dependencies import get_observability
from app.core.exception_handlers import register_exception_handlers
import app.models


@asynccontextmanager
async def lifespan(app : FastAPI):
    Base.metadata.create_all(bind = engine)
    
    try:
        yield
    finally:
        get_observability().shutdown()
    
app = FastAPI(
    title="Reasearch assistant",
    version = "0.1.0",
    lifespan=lifespan
)

app.include_router(document_router.router)
app.include_router(chat_router.router)
register_exception_handlers(app)

@app.get("/health")
def healthcheck():
    return {"status" : "ok"}


