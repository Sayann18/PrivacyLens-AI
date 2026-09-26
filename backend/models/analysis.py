from pydantic import BaseModel, Field


class Location(BaseModel):
    section: str | None = None
    page: int | None = None


class Finding(BaseModel):
    category: str
    severity: str
    title: str
    clause: str
    explanation: str
    why_it_matters: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    evidence_quality: str
    location: Location


class Section(BaseModel):
    title: str
    text: str
    page: int | None = None


class DocumentAnalysisResponse(BaseModel):
    source: str
    document_type: str
    classification_confidence: float = Field(ge=0, le=1)
    sections: list[Section]
    findings: list[Finding]
    top_things_to_know: list[str]
    overall_risk_score: int = Field(ge=0, le=100)
    overall_risk_level: str
    summary: str
    analysis_version: str
    cached: bool = False
