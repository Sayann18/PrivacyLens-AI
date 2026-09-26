from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from .enums import Confidence, Importance


class QualificationDisposition(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    ATTENTION = "ATTENTION"
    AMBIGUOUS = "AMBIGUOUS"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"


class FactQualification(BaseModel):

    fact_id: str
    domain: str
    category: str
    disposition: QualificationDisposition
    should_surface: bool = False
    importance: Importance = Importance.LOW
    confidence: Confidence = Confidence.MEDIUM
    reason: str
    triggers: List[str] = Field(default_factory=list)
    modifiers: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
