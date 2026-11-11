from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base,engine
from app.routers import document_router
import app.models


@asynccontextmanager
async def lifespan(app : FastAPI):
    Base.metadata.create_all(bind = engine)
    
    yield
    
app = FastAPI(
    title="Reasearch assistant",
    version = "0.1.0",
    lifespan=lifespan
)

app.include_router(document_router.router)

@app.get("/health")
def healthcheck():
    return {"status" : "ok"}


