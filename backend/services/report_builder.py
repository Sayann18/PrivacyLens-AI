from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from models.consumer_risk import ConsumerRiskAnalysis

from models.analysis_v2 import (
    AnalysisAssessment, AnalysisReport, AnalysisSummary, DocumentProfile, ExtractionInfo,
    Fact, PrivacyAnalysis, FinancialAnalysis, ContractAnalysis, Gap, Ambiguity, Recommendation,
)
from models.enums import AssessmentLevel, Confidence, Importance, ExtractionStatus
from models.normalized_document import NormalizedDocument
from services.document_classifier import ClassificationResult
from services.metadata_extractor import MetadataResult
from services.impact_engine import ImpactedFinding
from services.priority_engine import PriorityEngine


class ReportBuilder:
    def build(
        self,
        document: NormalizedDocument,
        classification: ClassificationResult,
        metadata: MetadataResult,
        privacy: PrivacyAnalysis,
        financial: FinancialAnalysis,
        contract: ContractAnalysis,
        gaps: list[Gap],
        ambiguities: list[Ambiguity],
        facts: list[Fact],
        evidence: list,
        impacted: list[ImpactedFinding],
        summary_text: str | None = None,
        risk_analysis: ConsumerRiskAnalysis | None = None,
        summary_used_llm: bool = False,
    ) -> AnalysisReport:
        priority = PriorityEngine()
        selected, _ = priority.select(impacted) if classification.is_consumer_document else ([], [])
        highlights = priority.highlights(impacted) if classification.is_consumer_document else []
        high_count = sum(1 for item in impacted if item.importance == Importance.HIGH)
        medium_count = sum(1 for item in impacted if item.importance == Importance.MEDIUM)
        if high_count:
            level = AssessmentLevel.REVIEW_RECOMMENDED
        elif medium_count >= 3:
            level = AssessmentLevel.MOSTLY_SAFE
        else:
            level = AssessmentLevel.NOTHING_SIGNIFICANT_IDENTIFIED
        assessment_text = {
            AssessmentLevel.REVIEW_RECOMMENDED: "Several items may warrant closer review based on the supplied wording and available evidence.",
            AssessmentLevel.MOSTLY_SAFE: "The document contains areas worth understanding, but no concentration of high-importance findings was identified by this analysis.",
            AssessmentLevel.NOTHING_SIGNIFICANT_IDENTIFIED: "No high-importance issue was identified by the structured checks applied to the supplied document.",
        }[level]
        extraction = ExtractionInfo(
            source_type=document.source_type,
            source_name=document.source_name,
            source_url=document.source_url,
            mime_type=document.mime_type,
            detected_file_type=document.detected_file_type,
            extraction_method=document.extraction_method,
            extraction_status=document.extraction_status,
            partial=document.partial,
            warnings=document.warnings,
            pages_total=len(document.pages) or None,
            pages_extracted=sum(1 for p in document.pages if p.text.strip()) or None,
            pages_failed=sum(1 for p in document.pages if p.warning) if document.pages else None,
        )
        profile = DocumentProfile(
            primary_type=classification.primary_type,
            secondary_types=classification.secondary_types,
            classification_confidence=classification.confidence,
            company=metadata.company,
            product=metadata.product,
            effective_date=metadata.effective_date,
            last_updated=metadata.last_updated,
            version=metadata.version,
            jurisdiction=metadata.jurisdiction,
        )
        key_points = [item.summary for item in highlights[:5]]
        recommendations = [
            Recommendation(
                title=f"Check {item.title.lower()}",
                description=f"Review the cited clause and any linked policy or account settings before relying on it. {item.summary}",
                importance=item.importance,
                category=item.category,
                evidence_ids=item.evidence_ids,
            )
            for item in selected[:5]
        ] if classification.is_consumer_document else []
        return AnalysisReport(
            id=str(uuid4()),
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
            document=profile,
            extraction=extraction,
            summary=AnalysisSummary(
                document_type_description=("General document" if classification.primary_type.value == "UNKNOWN" else classification.primary_type.value.replace("_", " ").title()),
                text=summary_text or " ".join(key_points[:3]),
                generated_by_ai=summary_used_llm,
                key_points=key_points,
                word_count=len(document.raw_text.split()),
            ),
            assessment=AnalysisAssessment(level=level, explanation=assessment_text, confidence=Confidence.HIGH if document.extraction_confidence >= 0.8 else Confidence.MEDIUM),
            highlights=highlights,
            privacy=privacy if classification.is_consumer_document else None,
            payments=financial if classification.is_consumer_document else None,
            contract=contract if classification.is_consumer_document else None,
            gaps=gaps,
            ambiguities=ambiguities,
            evidence=evidence,
            recommendations=recommendations,
            risk_analysis=risk_analysis,
        )
