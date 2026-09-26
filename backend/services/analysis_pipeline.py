from __future__ import annotations

import asyncio
import hashlib
from services.ambiguity_analyzer import AmbiguityAnalyzer
from services.cache import TTLCache
from services.contract_analyzer import ContractAnalyzer
from services.document_classifier import DocumentClassifier
from services.fact_extraction import FactExtractionService
from services.financial_analyzer import FinancialAnalyzer
from services.gap_analyzer import GapAnalyzer
from services.impact_engine import ImpactEngine
from services.fact_qualifier import FactQualifier
from services.metadata_extractor import DocumentMetadataExtractor
from services.privacy_analyzer import PrivacyAnalyzer
from services.report_builder import ReportBuilder
from services.summary_service import SummaryService
from services.consumer_risk_analyzer import ConsumerRiskAnalyzer
from services.sectionizer import Sectionizer
from utils.config import get_settings


class AnalysisPipeline:

    def __init__(self) -> None:
        ttl = get_settings().cache_ttl_seconds
        self.storage = TTLCache(ttl)
        self.analysis_cache = TTLCache(ttl)
        self.normalized_cache = TTLCache(ttl)
        self.classifier = DocumentClassifier()
        self.sectionizer = Sectionizer()
        self.metadata = DocumentMetadataExtractor()
        self.privacy = PrivacyAnalyzer()
        self.financial = FinancialAnalyzer()
        self.contract = ContractAnalyzer()
        self.gaps = GapAnalyzer()
        self.ambiguities = AmbiguityAnalyzer()
        self.impact = ImpactEngine()
        self.qualifier = FactQualifier()
        self.report = ReportBuilder()
        self.summary_service = SummaryService()
        self.risk_analyzer = ConsumerRiskAnalyzer()

    async def analyze(self, document):
        fingerprint = hashlib.sha256(document.raw_text.encode("utf-8")).hexdigest()
        cached_report = self.analysis_cache.get(fingerprint)
        if cached_report is not None:
            return cached_report
        cached_document = self.normalized_cache.get(fingerprint)
        if cached_document is None:
            self.normalized_cache.set(fingerprint, document)
        else:
            document = cached_document

        sections = self.sectionizer.sectionize(document)
        document = document.model_copy(update={"sections": sections})
        classification = self.classifier.classify(document)
        metadata = self.metadata.extract(document)
        from services.evidence_service import EvidenceService
        evidence_service = EvidenceService()
        fact_result = await FactExtractionService(evidence_service=evidence_service, use_llm=getattr(get_settings(), "llm_ready", getattr(get_settings(), "openai_ready", False))).extract(document, sections)
        privacy, financial, contract = await asyncio.gather(
            self.privacy.analyze(document, fact_result.facts),
            self.financial.analyze(document, fact_result.facts),
            self.contract.analyze(document, fact_result.facts),
        )
        qualifications = self.qualifier.qualify(fact_result.facts, evidence_service.get_all())
        gaps, ambiguities = await asyncio.gather(
            self.gaps.analyze(document, fact_result.facts),
            self.ambiguities.analyze(document, evidence_service),
        )
        relevant_gaps = [gap for gap in gaps if self.qualifier.relevant_gap(gap, document)]
        impacted = await self.impact.score(fact_result.facts, relevant_gaps, ambiguities, qualifications)
        summary_text, summary_used_llm = await self.summary_service.summarize(document.raw_text)
        risk_analysis = self.risk_analyzer.analyze(fact_result.facts, qualifications, relevant_gaps, ambiguities, classification.is_consumer_document)
        report = self.report.build(document, classification, metadata, privacy, financial, contract, relevant_gaps, ambiguities, fact_result.facts, evidence_service.get_all(), impacted, summary_text, risk_analysis, summary_used_llm)
        self.analysis_cache.set(fingerprint, report)
        self.storage.set(report.id, report)
        return report

    def get(self, analysis_id: str):
        return self.storage.get(analysis_id)
