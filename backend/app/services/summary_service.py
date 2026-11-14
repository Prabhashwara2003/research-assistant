import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.summary_generator import SummaryGenerator
from app.repositories.document_repository import DocumentRepository
from app.schemas.summary_schema import ResearchSummary

from app.core.observability import Observability
from app.core.exceptions import DocumentNotFoundError, DocumentNotReadyError


class SummaryService:

    @staticmethod
    def _read_saved_summary(summary_json: str) -> ResearchSummary:
        data = json.loads(summary_json)
        if "problem_statement" not in data:
            data["problem_statement"] = "Not available in this saved summary. Upload the paper again to generate one."
        return ResearchSummary.model_validate(data)
    
    def __init__(
        self,
        database : Session,
        summary_generator : SummaryGenerator,
        extracted_directory : Path,
        observability : Observability | None = None
    ):
        self.database = database
        self.summary_generator = summary_generator
        self.extracted_directory = extracted_directory
        self.observability = observability or Observability()
        self.document_repository = DocumentRepository(
            database
        )
        
    def generate_summary(
        self,
        document_id : str
    )->ResearchSummary:
        
        document = self.document_repository.get_by_id(
            document_id
        )
        
        if document is None:
            raise DocumentNotFoundError("Document not found")
        
        if document.summary_json is not None:
            return self._read_saved_summary(document.summary_json)
            
        if document.status != "indexed":
            raise DocumentNotReadyError("Document must be indexed before summarization")
        
        markdown_path = (
            self.extracted_directory/document_id/"document.md"
        )
        
        if not markdown_path.is_file():
            raise FileNotFoundError(
                "Extracted Markdown does not exist"
            )
        
        markdown = markdown_path.read_text(
            encoding="utf-8"
        )
        
        with self.observability.trace(
            "generate-research-summary",
            metadata={"document_id": document_id}
        ):
            summary = self.summary_generator.generate(
                markdown
            )
        
        self.document_repository.save_summary(
            document=document,
            summary_json=summary.model_dump_json()
        )
        
        return summary
    
    def get_summary(
        self,
        document_id : str
    )->ResearchSummary | None:
        document = self.document_repository.get_by_id(
            document_id
        )
        
        if document is None:
            raise DocumentNotFoundError("Document not found")
        
        if document.summary_json is None:
            return None
        
        return self._read_saved_summary(document.summary_json)
