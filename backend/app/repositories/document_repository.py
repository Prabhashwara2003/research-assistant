from sqlalchemy.orm import Session

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
