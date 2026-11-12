from app.models.document_image import DocumentImage

from sqlalchemy.orm import Session
from sqlalchemy import select

class ImageRepository :
    
    def __init__(self,database : Session):
        
        self.database = database
        
    def add_image(self, images : list[DocumentImage])->None:
        self.database.add_all(images)
        
    def find_by_id(
        self,
        image_id : str,
        document_id :str
        )->DocumentImage | None:
        
        statement = select(DocumentImage).where(
            DocumentImage.document_id == document_id,
            DocumentImage.image_id == image_id
        )
        
        return self.database.scalar(statement)
        
    def get_by_document(
        self,
        document_id: str
    ) -> list[DocumentImage]:

        statement = select(DocumentImage).where(
            DocumentImage.document_id == document_id
        )

        result = self.database.scalars(statement)

        return list(result.all())
