from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import ExtractionStatus
from .analysis_v2 import DocumentSection


class NormalizedPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    text: str = ""
    extraction_method: str
    ocr: bool = False
    warning: str | None = None


class NormalizedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    source_type: str
    source_name: str
    source_url: str | None = None
    mime_type: str | None = None
    detected_file_type: str
    raw_text: str = ""
    pages: list[NormalizedPage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    language: str = "unknown"
    character_count: int = Field(default=0, ge=0)
    extraction_method: str = "native"
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_status: ExtractionStatus = ExtractionStatus.COMPLETE
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
