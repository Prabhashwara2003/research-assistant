from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message

class MessageRepository:
    def __init__ (
        self,
        database : Session
    ):
        self.database = database
    
    def get_recent_messages(
        self,
        document_id : str,
        limit : int
    )-> list[Message]:
        
        statement = (
            select(Message)
            .where(Message.document_id == document_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        
        
        messages = list(
            self.database.scalars(statement).all()
        )
        
        messages.reverse()
        
        return messages
    
    def get_all_messages(
        self,
        document_id: str
    )->list[Message]:
        statement = (
            select(Message)
            .where(Message.document_id == document_id)
            .order_by(Message.id.asc())
        )
        
        return list(
            self.database.scalars(statement).all()
        )
        
    def save_exchange(
        self,
        document_id : str,
        question : str,
        answer : str
    )-> Message:
        
        user_message = Message(
            document_id=document_id,
            role = "user",
            content=question
        )
        
        assistant_message = Message(
            document_id=document_id,
            role="assistant",
            content=answer
        )
        
        try:
            self.database.add(user_message)
            self.database.add(assistant_message)

            self.database.commit()
            self.database.refresh(assistant_message)

            return assistant_message
        
        except Exception:
            self.database.rollback()
            raise