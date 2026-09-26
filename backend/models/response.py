from datetime import datetime
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published_at: str | None = None
    relevance: float = Field(ge=0, le=1)
    stance: str = "neutral"


class VerificationResponse(BaseModel):
    claim: str
    verdict: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    evidence: list[EvidenceItem]
    sources_checked: list[str]
    cached: bool = False
    generated_at: datetime


class ExtractedContentResponse(BaseModel):
    source: str
    text: str
    character_count: int
