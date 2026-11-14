from fastapi import APIRouter,Depends,HTTPException

from app.ai.dependencies import get_chat_service

from app.schemas.chat_schema import (
    ChatResponse,
    ChatRequest,
    MessageResponse
)

from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/api/documents/{document_id}/messages",
    tags=["Chat"]
)

@router.post(
    "",
    response_model=ChatResponse,
    status_code=201
)
def send_message(
    document_id : str,
    request : ChatRequest,
    service : ChatService = Depends(get_chat_service)
):
    return service.ask_question(document_id=document_id, question=request.question)
        
@router.get(
    "",
    response_model=list[MessageResponse]
)
def get_message(
    document_id : str,
    service : ChatService = Depends(get_chat_service)
):
    return service.get_chat_history(document_id=document_id)
