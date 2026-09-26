from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RiskArea(BaseModel):
    area: str
    level: RiskLevel
    title: str
    summary: str
    why_it_matters: str
    evidence_ids: List[str] = Field(default_factory=list)


class ConsumerRiskAnalysis(BaseModel):
    overall_level: RiskLevel
    title: str
    explanation: str
    areas: List[RiskArea] = Field(default_factory=list)
    scope: str = "Based only on the supplied document content and available evidence."
    disclaimer: str = "This is an evidence-based attention assessment, not a legal determination or guarantee of safety."
