from datetime import datetime,timezone

from sqlalchemy import Column,DateTime,Text,String

from app.core.database import Base

class Document(Base):
    
    __tablename__= "documents"
    
    id = Column(String(36), primary_key=True)

    filename = Column(String(255), nullable=False)

    file_path = Column(String(500), nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="pending"
    )

    summary_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )