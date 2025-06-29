from pydantic import BaseModel
from typing import List, Optional


class BoundingBox(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class Word(BaseModel):
    text: str
    bbox: BoundingBox


class Page(BaseModel):
    words: List[Word]


class MedicalDocument(BaseModel):
    document_id: Optional[str] = None
    pages: List[Page]
