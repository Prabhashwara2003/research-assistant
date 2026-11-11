
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_upload_directory
from app.core.database import get_db
from app.schemas.document_schema import DocumentResponse
from app.services.document_service import DocumentService


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
