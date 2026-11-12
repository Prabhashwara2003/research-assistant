from sqlalchemy import Column,Text,String,Boolean,ForeignKey,Integer

from app.core.database import Base

class DocumentImage(Base):
    
    __tablename__="document_image"
    
    image_id = Column(
        String(150),
        primary_key=True
    )

    document_id = Column(
        String(36),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    page_number = Column(
        Integer,
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    image_type = Column(String(100))
    caption = Column(Text)
    description = Column(Text)
    raw_description = Column(Text)
    source_context = Column(Text)

    decorative_candidate = Column(
        Boolean,
        nullable=False,
        default=False
    )

    description_status = Column(String(30))
    bounding_box = Column(Text)