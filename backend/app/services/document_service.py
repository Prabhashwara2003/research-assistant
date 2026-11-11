
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository


class DocumentService:

    def __init__(
        self,
        database: Session,
        upload_directory: Path
    ):
        self.database = database
        self.upload_directory = upload_directory

        self.document_repository = DocumentRepository(database)

    def upload_document(self, file: UploadFile) -> Document:

        # 1. Validate the filename.
        filename = file.filename

        if filename is None or not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # 2. Create a unique document identifier.
        document_id = str(uuid4())

        # Never use the original filename as our storage filename.
        stored_filename = f"{document_id}.pdf"

        # 3. Prepare the storage location.
        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = self.upload_directory / stored_filename

        # 4. Calculate the upload size limit.
        maximum_size = settings.max_pdf_size_mb * 1024 * 1024

        total_size = 0
        first_chunk = True

        try:
            # 5. Read the uploaded file in small blocks.
            with open(file_path, "wb") as output_file:

                while True:
                    chunk = file.file.read(1024 * 1024)

                    if not chunk:
                        break

                    if first_chunk:
                        if not chunk.startswith(b"%PDF-"):
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid PDF file"
                            )

                        first_chunk = False

                    total_size += len(chunk)

                    if total_size > maximum_size:
                        raise HTTPException(
                            status_code=413,
                            detail="PDF exceeds the upload size limit"
                        )

                    output_file.write(chunk)

            if total_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )

            # 6. Create the database record.
            document = Document(
                id=document_id,
                filename=Path(filename).name,
                file_path=str(file_path),
                status="pending"
            )

            # 7. Save metadata using our repository.
            saved_document = self.document_repository.create(document)

            return saved_document

        except Exception:
            # If anything fails, undo the database transaction
            # and remove any partially saved PDF.
            self.database.rollback()

            if file_path.exists():
                file_path.unlink()

            raise

        finally:
            file.file.close()

    def get_document(self, document_id: str) -> Document:

        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return document
