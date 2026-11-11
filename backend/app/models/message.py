from datetime import datetime,timezone

from sqlalchemy import Column,Text,String,DateTime,Integer,ForeignKey

from app.core.database import Base

class Message(Base):
    
    __tablename__="messages"
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    document_id = Column(
        String(36),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    role = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )