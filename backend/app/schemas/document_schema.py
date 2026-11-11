from datetime import datetime

from pydantic import BaseModel,ConfigDict

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    summary_json: str | None
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )