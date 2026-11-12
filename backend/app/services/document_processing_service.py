import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session
from app.ai.pdf_extractor import PDFExtractor
from app.ai.text_chuncker import TextChunker
from app.ai.vector_store import VectorStoreManager

from app.models.document import Document
from app.models.document_image import DocumentImage

from app.repositories.image_repository import ImageRepository
from app.repositories.document_repository import DocumentRepository

class DocumentProcessingService:
    
    
    def __init__(
        self,
        database : Session,
        extractor : PDFExtractor,
        chunker : TextChunker,
        vector_store : VectorStoreManager,
        extracted_directory : Path
        
    ):
        self.database = database
        self.extractor = extractor
        self.chunker = chunker
        self.vector_store = vector_store
        self.extracted_directory = extracted_directory
        self.document_repository = DocumentRepository(database)
        self.image_repository = ImageRepository(database)
        
    def process(self,document_id : str )-> int:
        
        document = self.document_repository.get_by_id(document_id)
        
        if document is None :
            raise ValueError("Document not found")
        
        claimed = self.document_repository.claim_for_processing(
            document_id
        )
        
        if not claimed :
            raise ValueError(
                "Document cannot be processed in its current state"
            )
        
        self.extracted_directory.mkdir(
            parents = True,
            exist_ok=True
        )
        
        final_directory = self.extracted_directory/document_id
        moved_output = False
        
        try :
            with TemporaryDirectory(
                dir=self.extracted_directory
                
            ) as temporary_path:
                
                working_directory = Path(temporary_path)
                
                result = self.extractor.extract(
                    pdf_path = Path(document.file_path),
                    document_id = document_id,
                    output_directory = working_directory
                )
                
                if not result.documents:
                    raise ValueError("No extractable content found")
                
                markdown_path = working_directory/"document.md"
                
                markdown_path.write_text(
                    result.markdown,
                    encoding="utf-8"
                )
                
                image_records = []
                
                for image in result.images:
                    
                    final_image_path = (
                        final_directory / "images" / f"{image.image_id}.png"
                    )
                    
                    image_record = DocumentImage(
                        image_id=image.image_id,
                        document_id=image.document_id,
                        page_number=image.page_number,
                        file_path=str(final_image_path),
                        image_type=image.image_type,
                        caption=image.caption,
                        description=image.description,
                        raw_description=image.raw_description,
                        source_context=image.source_context,
                        decorative_candidate=image.decorative_candidate,
                        description_status=image.description_status,
                        bounding_box=json.dumps(image.bounding_box)
                    )
                    
                    image_records.append(image_record)
                    
                chunks = self.chunker.split(result.documents)
                
                if not chunks:
                    raise ValueError("No searchable chunks were created")
                
                self.vector_store.index_document(
                    document_id=document_id,
                    chunks=chunks
                )
                    
                if final_directory.exists():
                    raise ValueError("Extarction output already exists")
                
                working_directory.rename(final_directory)
                moved_output = True
                
                self.image_repository.add_image(image_records)
                
                document.status = "indexed"
                
                self.database.commit()
                
                return len(chunks)
            
        except Exception:
            
            self.database.rollback()
            
            self.vector_store.remove_document(document_id)
            
            if moved_output and final_directory.exists():
                shutil.rmtree(final_directory)
            
            self.document_repository.update_status(
                document_id,
                "failed"
            )
            
            raise
        
