from datetime import datetime

from pydantic import BaseModel,Field,ConfigDict

class ChatRequest(BaseModel):
    question : str = Field(
        min_length=1,
        max_length=2000
    )
    
class SourceReference(BaseModel):
    page: int
    image_id: str | None = None
    
class ChatResponse(BaseModel):
    message_id: int
    answer: str
    sources: list[SourceReference]
    
class MessageResponse(BaseModel):
    id: int
    document_id: str
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)