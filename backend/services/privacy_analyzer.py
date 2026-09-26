from __future__ import annotations

from dataclasses import dataclass

from models.analysis_v2 import Fact, PrivacyAnalysis, PrivacyAreaReport
from models.enums import DisclosureStatus, FactCategory, Confidence
from models.normalized_document import NormalizedDocument


@dataclass(frozen=True)
class _Area:
    name: str
    categories: tuple[FactCategory, ...]
    impact: str


class PrivacyAnalyzer:
    AREAS = (
        _Area("Data collected", (FactCategory.DATA_COLLECTION,), "This describes what personal information the service says it collects."),
        _Area("Purpose of use", (FactCategory.DATA_USAGE,), "This describes stated purposes for using information."),
        _Area("Third-party sharing", (FactCategory.DATA_SHARING,), "This describes organizations or categories the document says may receive information."),
        _Area("Data sale or disclosure", (FactCategory.DATA_SHARING,), "This area covers sale or other disclosures of personal information."),
        _Area("Tracking", (FactCategory.TRACKING,), "This describes cookies, pixels, analytics, or similar tracking technologies."),
        _Area("Advertising", (FactCategory.ADVERTISING,), "This describes advertising or marketing uses of information."),
        _Area("AI/model training", (FactCategory.AI_USAGE,), "This describes stated use of information for AI or model-related purposes."),
        _Area("Retention", (FactCategory.RETENTION,), "This describes how long or under what conditions information is retained."),
        _Area("Deletion", (FactCategory.DELETION,), "This describes deletion or erasure of information or accounts."),
        _Area("User rights", (), "This area covers access, correction, portability, objection, and similar user rights."),
        _Area("International transfers", (), "This area covers transfers of information across countries or regions."),
        _Area("Security measures", (), "This area covers stated safeguards for information."),
        _Area("Children/minors", (), "This area covers provisions concerning children or minors."),
        _Area("Automated decisions", (), "This area covers automated decision-making or profiling."),
    )

    KEYWORDS = {
        "User rights": ("access your", "delete your", "correct your", "portability", "opt out", "right to"),
        "International transfers": ("international transfer", "transfer outside", "cross-border", "outside your country"),
        "Security measures": ("security measures", "encryption", "safeguards", "protect personal", "security practices"),
        "Children/minors": ("children", "child", "minor", "under 13", "under 16"),
        "Automated decisions": ("automated decision", "profiling", "solely automated"),
    }

    def _area(self, area: _Area, facts: list[Fact], text: str) -> PrivacyAreaReport:
        matching = [f for f in facts if f.category in area.categories]
        keyword_hit = any(k in text.lower() for k in self.KEYWORDS.get(area.name, ()))
        status = DisclosureStatus.DISCLOSED if matching or keyword_hit else DisclosureStatus.NOT_FOUND
        if matching and any("may" in (f.object_ or "").lower() and len(f.object_) > 120 for f in matching):
            status = DisclosureStatus.AMBIGUOUS
        confidence = Confidence.HIGH if matching else (Confidence.MEDIUM if keyword_hit else Confidence.LOW)
        evidence_ids = [eid for fact in matching for eid in fact.evidence_ids]
        if status == DisclosureStatus.NOT_FOUND:
            impact = "The document did not contain a clearly identified clause for this area. This means the information was not found in the supplied text, not that it is absent in practice."
        else:
            impact = area.impact
        return PrivacyAreaReport(area_name=area.name, status=status, facts=matching, evidence_ids=evidence_ids, user_impact=impact, confidence=confidence)

    async def analyze(self, document: NormalizedDocument, facts: list[Fact]) -> PrivacyAnalysis:
        reports = {area.name: self._area(area, facts, document.raw_text) for area in self.AREAS}
        return PrivacyAnalysis(
            data_collected=reports["Data collected"], purpose_of_use=reports["Purpose of use"],
            third_party_sharing=reports["Third-party sharing"], data_sale_or_disclosure=reports["Data sale or disclosure"],
            tracking=reports["Tracking"], advertising=reports["Advertising"], ai_model_training=reports["AI/model training"],
            retention=reports["Retention"], deletion=reports["Deletion"], user_rights=reports["User rights"],
            international_transfers=reports["International transfers"], security_measures=reports["Security measures"],
            children_minors=reports["Children/minors"], automated_decision_making=reports["Automated decisions"],
        )
