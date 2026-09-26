from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    AssessmentLevel,
    AnalysisStatus,
    Confidence,
    DisclosureStatus,
    DocumentType,
    EvidenceStrength,
    ExtractionStatus,
    FactCategory,
    FinancialClarity,
    Importance,
)


class Evidence(BaseModel):
    evidence_id: str
    source_document: str
    source_url: Optional[str] = None
    page: Optional[int] = Field(default=None, ge=1)
    section: Optional[str] = None
    exact_quote: str
    normalized_quote: str
    evidence_type: EvidenceStrength = EvidenceStrength.DIRECT
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Fact(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fact_id: str
    category: FactCategory
    subject: str
    action: str
    object_: str = Field(validation_alias="object", serialization_alias="object_")
    purpose: Optional[str] = None
    recipient: Optional[str] = None
    conditions: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    status: DisclosureStatus = DisclosureStatus.DISCLOSED
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Finding(BaseModel):
    finding_id: Optional[str] = None
    category: FactCategory
    title: str
    explanation: str
    why_it_matters: str
    importance: Importance
    confidence: Confidence
    evidence_ids: List[str] = Field(default_factory=list)
    status: DisclosureStatus


class DocumentProfile(BaseModel):
    primary_type: DocumentType = DocumentType.UNKNOWN
    secondary_types: List[DocumentType] = Field(default_factory=list)
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    company: Optional[str] = None
    product: Optional[str] = None
    effective_date: Optional[str] = None
    last_updated: Optional[str] = None
    version: Optional[str] = None
    jurisdiction: Optional[str] = None


class DocumentQuality(BaseModel):
    character_count: int = Field(default=0, ge=0)
    section_count: int = Field(default=0, ge=0)
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    meaningful_text_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    is_scanned: bool = False


class ExtractionInfo(BaseModel):
    source_type: str
    source_name: str
    source_url: Optional[str] = None
    mime_type: Optional[str] = None
    detected_file_type: str
    extraction_method: str
    extraction_status: ExtractionStatus = ExtractionStatus.COMPLETE
    partial: bool = False
    warnings: List[str] = Field(default_factory=list)
    pages_total: Optional[int] = Field(default=None, ge=0)
    pages_extracted: Optional[int] = Field(default=None, ge=0)
    pages_failed: Optional[int] = Field(default=None, ge=0)


class DocumentSection(BaseModel):
    section_id: str
    title: str
    text: str
    page: Optional[int] = Field(default=None, ge=1)
    section_type: Optional[str] = None


class PrivacyAreaReport(BaseModel):
    area_name: str
    status: DisclosureStatus
    facts: List[Fact] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    user_impact: str
    confidence: Confidence = Confidence.MEDIUM


class PrivacyAnalysis(BaseModel):
    data_collected: PrivacyAreaReport
    purpose_of_use: PrivacyAreaReport
    third_party_sharing: PrivacyAreaReport
    data_sale_or_disclosure: PrivacyAreaReport
    tracking: PrivacyAreaReport
    advertising: PrivacyAreaReport
    ai_model_training: PrivacyAreaReport
    retention: PrivacyAreaReport
    deletion: PrivacyAreaReport
    user_rights: PrivacyAreaReport
    international_transfers: Optional[PrivacyAreaReport] = None
    security_measures: Optional[PrivacyAreaReport] = None
    children_minors: Optional[PrivacyAreaReport] = None
    automated_decision_making: Optional[PrivacyAreaReport] = None


class FinancialAreaReport(BaseModel):
    area_name: str
    clarity: FinancialClarity
    what_document_says: str
    why_it_matters: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM
    what_to_check: Optional[str] = None


class FinancialAnalysis(BaseModel):
    subscription: FinancialAreaReport
    automatic_renewal: FinancialAreaReport
    billing_frequency: FinancialAreaReport
    trial_period: FinancialAreaReport
    trial_conversion: FinancialAreaReport
    listed_prices: FinancialAreaReport
    additional_fees: FinancialAreaReport
    cancellation_requirements: FinancialAreaReport
    cancellation_deadline: FinancialAreaReport
    refund_policy: FinancialAreaReport
    refund_exceptions: FinancialAreaReport
    price_changes: FinancialAreaReport


class ContractAreaReport(BaseModel):
    area_name: str
    status: DisclosureStatus
    plain_language_explanation: str
    potential_user_impact: str
    conditions_or_exceptions: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


class ContractAnalysis(BaseModel):
    liability_limitation: ContractAreaReport
    indemnification: ContractAreaReport
    arbitration: ContractAreaReport
    class_action_waiver: ContractAreaReport
    termination: ContractAreaReport
    account_suspension: ContractAreaReport
    content_ownership: ContractAreaReport
    license_granted_to_company: ContractAreaReport
    governing_law: ContractAreaReport
    dispute_resolution: ContractAreaReport
    unilateral_changes: ContractAreaReport


class Gap(BaseModel):
    gap_id: Optional[str] = None
    category: str
    description: str
    importance: Importance
    evidence: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


class Ambiguity(BaseModel):
    ambiguity_id: Optional[str] = None
    text: str
    category: str
    explanation: str
    importance: Importance = Importance.MEDIUM
    evidence: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


class Recommendation(BaseModel):
    recommendation_id: Optional[str] = None
    title: str
    description: str
    importance: Importance
    category: str
    evidence_ids: List[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    document_type_description: str
    text: str = ""
    generated_by_ai: bool = False
    key_points: List[str] = Field(default_factory=list)
    word_count: int = Field(default=0, ge=0)


class AnalysisAssessment(BaseModel):
    level: AssessmentLevel
    explanation: str
    confidence: Confidence = Confidence.MEDIUM


class Highlight(BaseModel):
    title: str
    importance: Importance
    summary: str
    why_it_matters: str
    evidence_id: Optional[str] = None
    confidence: Confidence = Confidence.HIGH


class AnalysisReport(BaseModel):
    id: str
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    created_at: datetime
    document: DocumentProfile
    extraction: ExtractionInfo
    summary: AnalysisSummary
    assessment: AnalysisAssessment
    highlights: List[Highlight] = Field(default_factory=list)
    privacy: Optional[PrivacyAnalysis] = None
    payments: Optional[FinancialAnalysis] = None
    contract: Optional[ContractAnalysis] = None
    gaps: List[Gap] = Field(default_factory=list)
    ambiguities: List[Ambiguity] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    risk_analysis: Optional["ConsumerRiskAnalysis"] = None


from .consumer_risk import ConsumerRiskAnalysis
AnalysisReport.model_rebuild()
