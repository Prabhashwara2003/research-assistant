from dataclasses import dataclass,field
from pathlib import Path

from langchain_core.documents import Document

@dataclass
class ExtractedImage :
    image_id: str
    document_id: str
    page_number: int
    file_path: Path

    image_type: str = "unknown"
    caption: str = ""
    description: str = ""
    raw_description: str = ""
    source_context: str = ""

    decorative_candidate: bool = False
    description_status: str = "needs_review"

    bounding_box: list[float] = field(
        default_factory=list
    )
    
@dataclass
class ExtractionResult :
    markdown : str
    documents : list[Document]
    images : list[ExtractedImage]
