
from pathlib import Path
from fastapi import HTTPException
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_upload_directory
from app.core.database import get_db
from app.schemas.document_schema import DocumentResponse
from app.services.document_service import DocumentService
from app.ai.dependencies import get_documents_processor
from app.services.document_processing_service import (
    DocumentProcessingService
)
from app.repositories.image_repository import ImageRepository

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=201
)
def upload_document(
    file: UploadFile = File(...),
    database: Session = Depends(get_db),
    upload_directory: Path = Depends(get_upload_directory)
):
    service = DocumentService(
        database=database,
        upload_directory=upload_directory
    )

    document = service.upload_document(file)

    return document


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: str,
    database: Session = Depends(get_db),
    upload_directory: Path = Depends(get_upload_directory)
):
    service = DocumentService(
        database=database,
        upload_directory=upload_directory
    )

    document = service.get_document(document_id)

    return document


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    database: Session = Depends(get_db),
    upload_directory: Path = Depends(get_upload_directory)
):
    service = DocumentService(
        database=database,
        upload_directory=upload_directory
    )

    document = service.get_document(document_id)

    file_path = Path(document.file_path)

    if not file_path.is_file():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.filename,
        content_disposition_type="inline"
    )

@router.post("/{document_id}/process")
def process_document(
    document_id:str,
    processor:DocumentProcessingService=Depends(
        get_documents_processor
    )
):
    try:
        chunk_count =processor.process(document_id)
        
        return{
            "document_id" : document_id,
            "status" : "indexed",
            "chunk_count" : chunk_count
        }
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document processing failed"
        )
    
@router.get("/{document_id}/images/{image_id}")
def get_document_image(
    document_id : str,
    image_id : str,
    database : Session = Depends(get_db)
):
    repository = ImageRepository(database)
    
    image = repository.find_by_id(
        document_id=document_id,
        image_id=image_id
    )
    
    if image is None:
        raise HTTPException(
            status_code=404,
            detail="image not found"
        )
    image_path = Path(image.file_path)
    
    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image file is missing"
        )
    return FileResponse(
        path=image_path,
        media_type="image/png"
    )
