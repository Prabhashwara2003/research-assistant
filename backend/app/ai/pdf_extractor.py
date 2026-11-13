from collections import defaultdict

from pathlib import Path

from typing import Protocol

import re

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption
)

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionVlmOptions
)

from docling_core.types.doc import (
    PictureItem,
    TableItem,
    DocItemLabel
)

from langchain_core.documents import Document

from app.ai.extraction_model import (
    ExtractedImage,
    ExtractionResult
)

PICTURE_PROMPT = """
Identify the main subject of this image for document search.

For charts and graphs:
Describe what the chart is about and what categories,
questions, or variables it represents.

For diagrams:
Identify the system, concept, or process illustrated.

For photographs:
Identify the main subject or activity.

Ignore interface text such as "Copy chart".

Do not include numbers, percentages, quantities,
statistics, or conclusions about the results.

Do not invent information that is not visible.

Write one clear, informative sentence about the image.
Do not use markdown.
"""

class PDFExtractor(Protocol):
    
    def extract(
        self,
        pdf_path : Path,
        document_id : str,
        output_directory : Path
    )->ExtractionResult:
        ...
        
class DoclingPDFExtractor :
    
    def __init__(
        self,
        max_pages : int,
        enable_description : bool,
        picture_model : str
    ):
        self.max_pages = max_pages
        
        options = PdfPipelineOptions()
        
        options.images_scale = 2.0
        options.generate_picture_images = True
        options.do_picture_classification = True
        options.do_chart_extraction = False
        options.do_picture_description = enable_description
        
        if enable_description:
            options.picture_description_options = (
                PictureDescriptionVlmOptions(
                    repo_id=picture_model,
                    prompt=PICTURE_PROMPT,
                    picture_area_threshold=0.03,
                    generation_config={
                        "max_new_tokens": 128,
                        "do_sample": False,
                        "repetition_penalty": 1.1
                    }
                )
            )
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF : PdfFormatOption(
                    pipeline_options=options
                )
            }
        )
    
    def clean_description(self, text: str) -> str:

        text = re.sub(r"[#*`>]+", " ", text or "")
        text = re.sub(r"\s+", " ", text).strip()

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        return " ".join(sentences[:2])[:300]

    def get_description(self, picture) -> str:

        metadata = getattr(picture, "meta", None)

        if metadata is not None:
            description = getattr(
                metadata,
                "description",
                None
            )

            if description is not None:
                text = getattr(
                    description,
                    "text",
                    ""
                )

                return self.clean_description(text)

        return ""
    
    def get_picture_type(self, picture) -> str:

        metadata = getattr(picture, "meta", None)

        if metadata is not None:
            classification = getattr(
                metadata,
                "classification",
                None
            )

            predictions = getattr(
                classification,
                "predictions",
                None
            )

            if predictions:
                return str(predictions[0].class_name)

        return "unknown"
    
    def is_description_useful(
        self,
        description: str
    ) -> bool:

        text = description.strip().lower()

        bad_descriptions = {
            "image",
            "chart",
            "graph",
            "picture",
            "screenshot",
            "copy chart",
            "no description"
        }

        if not text:
            return False

        if text.rstrip(".") in bad_descriptions:
            return False

        if len(text.split()) < 6:
            return False

        if text.startswith("copy chart"):
            return False

        return True
    
    
    def get_nearby_context(
        self,
        items: list,
        picture_index: int,
        page_number: int
    ) -> str:

        paragraphs = []

        for index in range(picture_index - 1, -1, -1):

            element = items[index][0]

            if isinstance(element, PictureItem):
                break

            provenance = getattr(element, "prov", None)

            if not provenance:
                continue

            if provenance[0].page_no != page_number:
                break

            if element.label in (
                DocItemLabel.PAGE_HEADER,
                DocItemLabel.PAGE_FOOTER
            ):
                continue

            text = getattr(element, "text", "")

            if not text:
                continue

            paragraphs.insert(0, text.strip())

            if len(paragraphs) >= 2:
                break

        return " ".join(paragraphs)
    
    def visual_signature(self, image) -> str:

        grayscale = image.convert("L")
        grayscale = grayscale.resize((16, 16))

        pixels = list(grayscale.getdata())
        average = sum(pixels) / len(pixels)

        return "".join(
            "1" if pixel > average else "0"
            for pixel in pixels
        )
        
    def find_decorative_images(
        self,
        doc
    ) -> set[str]:

        clusters = []

        for element, _ in doc.iterate_items():

            if not isinstance(element, PictureItem):
                continue

            if not element.prov:
                continue

            image = element.get_image(doc)

            if image is None:
                continue

            signature = self.visual_signature(image)
            aspect_ratio = image.width / image.height
            page_number = element.prov[0].page_no

            matched_cluster = None

            for cluster in clusters:
                distance = sum(
                    a != b
                    for a, b in zip(
                        signature,
                        cluster["signature"]
                    )
                )

                ratio_difference = abs(
                    aspect_ratio - cluster["aspect_ratio"]
                ) / cluster["aspect_ratio"]

                if distance <= 12 and ratio_difference < 0.1:
                    matched_cluster = cluster
                    break

            if matched_cluster is None:
                clusters.append({
                    "signature": signature,
                    "aspect_ratio": aspect_ratio,
                    "items": [(element, page_number)]
                })
            else:
                matched_cluster["items"].append(
                    (element, page_number)
                )

        decorative_refs = set()

        for cluster in clusters:
            pages = set()

            for _, page_number in cluster["items"]:
                pages.add(page_number)

            if len(pages) >= 3:
                for element, _ in cluster["items"]:
                    decorative_refs.add(element.self_ref)

        return decorative_refs
    
    def extract(
        self,
        pdf_path : Path,
        document_id : str,
        output_directory : Path
    )->ExtractionResult:
        result = self.converter.convert(pdf_path)
        doc = result.document
        
        if len(doc.pages) > self.max_pages:
            raise ValueError("PDF exceeds the allowed page count")
        
        image_directory = output_directory/"images"
        image_directory.mkdir(
            parents = True,
            exist_ok=True
        ) 
        
        items = list(doc.iterate_items())
        
        decorative_refs = self.find_decorative_images(doc)
        
        page_counter = defaultdict(int)
        markdown_parts = []
        extracted_documents =[]
        extracted_images = []
        
        for index,(element,_) in enumerate(items):
            provenance = getattr(element,"prov",None)
            
            if not provenance:
                continue
            
            page_number = provenance[0].page_no
            content = ""
            image_ids = []
            
            if isinstance(element,PictureItem):
                
                image = element.get_image(doc)
            
                if image is None:
                    continue
            
                page_counter[page_number] += 1
                
                image_id = (
                    f"{document_id}_p{page_number}_img"
                    f"{page_counter[page_number]}"
                )
                
                image_path = (
                    image_directory/f"{image_id}.png"
                )
                
                image.save(image_path)
                
                image_type = self.get_picture_type(element)
                
                raw_description = self.get_description(element)
                
                useful = self.is_description_useful(raw_description)
                
                description = (
                    raw_description if useful else ""
                )
                
                try:
                    caption = element.caption_text(doc)
                except Exception:
                    caption=""
                
                nearby_context = self.get_nearby_context(
                    items,
                    index,
                    page_number
                )
                
                decorative = (
                    element.self_ref in decorative_refs
                    or image_type.lower() in {"logo","icon"}
                )
                
                bbox = provenance[0].bbox
                
                extracted_images.append(
                    ExtractedImage(
                        image_id=image_id,
                        document_id=document_id,
                        page_number=page_number,
                        file_path=image_path,
                        image_type=image_type,
                        caption=caption,
                        description=description,
                        raw_description=raw_description,
                        source_context=nearby_context,
                        decorative_candidate=decorative,
                        description_status=("usable" if useful else "needs_review"),
                        bounding_box =[bbox.l,bbox.t,bbox.r,bbox.b]
                    )
                )
                
                lines = [
                    f"[IMAGE : {image_id}]",
                    f"Type : {image_type}",
                    f"Page : {page_number}",
                    f"Decorative canditate : {decorative}"
                ]
                if caption:
                    lines.append(f"Caption : {caption}")
                
                if description:
                    lines.append(f"Visual description: {description}")
                
                if nearby_context:
                    lines.append(f"Nearby source text: {nearby_context}")
                
                lines.append("Original image available for visual analysis")
                
                lines.append("[/IMAGE]")
                
                content = "\n".join(lines)
                
                image_ids = [image_id]
            
            elif isinstance(element,TableItem):
                content = element.export_to_markdown(doc)
                
            else:
                text = getattr(element,"text","")
                
                if not text:
                    continue
                text = text.strip()
                
                if element.label == DocItemLabel.TITLE :
                    content = f"#{text}"
                    
                elif element.label == DocItemLabel.SECTION_HEADER :
                    content = f"##{text}"
                    
                else:
                    content = text
                    
            if not content.strip():
                continue
            
            markdown_parts.append(content)
            
            extracted_documents.append(
                
                Document(
                    page_content=content,
                    metadata={
                        "document_id": document_id,
                        "page": page_number,
                        "image_ids": image_ids,
                        "content_type": (
                            "image"
                            if image_ids
                            else "text"
                        )
                    }
                )
            )
        
        markdown = "\n\n".join(markdown_parts)
        
        return ExtractionResult(
            markdown=markdown,
            documents= extracted_documents,
            images= extracted_images
        )
                
