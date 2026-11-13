from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models.document import Document

class DocumentRepository:
    
    def __init__(self,database : Session):
        self.database = database
        
    def create(self,document : Document) -> Document:
        self.database.add(document)
        self.database.commit()
        self.database.refresh(document)
        
        return document
    
    def get_by_id(self,document_id : str)-> Document | None:
        document = self.database.get(Document,document_id)
        
        return document
    def claim_for_processing(self,document_id : str)->bool:
        statement = (
            update(Document).where(Document.id == document_id).where(Document.status.in_(["pending","failed"])).values(status="processing")
        )
        result = self.database.execute(statement)
        self.database.commit()
        
        return result.rowcount == 1
    
    def update_status(
        self,
        document_id:str,
        status:str
    )->None:
        document = self.get_by_id(document_id)
        
        if document is None:
            raise ValueError("document not found")
        
        document.status = status
        
        self.database.commit()
        
    def save_summary(
        self,
        document : Document,
        summary_json : str
    )-> None:
        document.summary_json = summary_json
        document.status = "completed"
        
        self.database.commit()