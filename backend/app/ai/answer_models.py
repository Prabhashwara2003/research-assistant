from dataclasses import dataclass


@dataclass
class GeneratedAnswer:
    text: str
    attached_image_ids: list[str]
