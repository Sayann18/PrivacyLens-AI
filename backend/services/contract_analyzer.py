from __future__ import annotations

from models.analysis_v2 import ContractAnalysis, ContractAreaReport, Fact
from models.enums import DisclosureStatus, FactCategory, Confidence
from models.normalized_document import NormalizedDocument


class ContractAnalyzer:
    AREAS = {
        "liability_limitation": ("Liability limitation", FactCategory.LIABILITY),
        "indemnification": ("Indemnification", FactCategory.LIABILITY),
        "arbitration": ("Arbitration", FactCategory.ARBITRATION),
        "class_action_waiver": ("Class-action waiver", FactCategory.ARBITRATION),
        "termination": ("Termination", FactCategory.TERMINATION),
        "account_suspension": ("Account suspension", FactCategory.TERMINATION),
        "content_ownership": ("Content ownership", FactCategory.CONTENT_LICENSE),
        "license_granted_to_company": ("License granted to company", FactCategory.CONTENT_LICENSE),
        "governing_law": ("Governing law", FactCategory.GOVERNING_LAW),
        "dispute_resolution": ("Dispute resolution", FactCategory.ARBITRATION),
        "unilateral_changes": ("Unilateral changes", FactCategory.TERMINATION),
    }

    KEYWORDS = {
        "Class-action waiver": ("class action", "class-action"),
        "Unilateral changes": ("change these terms", "modify these terms", "at our discretion", "from time to time"),
    }

    def _report(self, name: str, category: FactCategory, facts: list[Fact], text: str) -> ContractAreaReport:
        matching = [f for f in facts if f.category == category]
        lower = text.lower()
        hit = any(k in lower for k in self.KEYWORDS.get(name, ()))
        status = DisclosureStatus.DISCLOSED if matching or hit else DisclosureStatus.NOT_FOUND
        if matching and any("may" in (f.object_ or "").lower() and "terminate" in (f.object_ or "").lower() for f in matching):
            status = DisclosureStatus.AMBIGUOUS
        explanation = matching[0].object_ if matching else ("The document contains wording relevant to this area." if hit else "No clearly matching clause was found in the supplied document.")
        impact = "This provision describes contractual rights, obligations, or dispute mechanisms that may affect how the agreement operates."
        ids = [eid for fact in matching for eid in fact.evidence_ids]
        confidence = Confidence.HIGH if matching else (Confidence.MEDIUM if hit else Confidence.LOW)
        return ContractAreaReport(area_name=name, status=status, plain_language_explanation=explanation[:1200], potential_user_impact=impact, conditions_or_exceptions=[], evidence_ids=ids, confidence=confidence)

    async def analyze(self, document: NormalizedDocument, facts: list[Fact]) -> ContractAnalysis:
        values = {key: self._report(label, category, facts, document.raw_text) for key, (label, category) in self.AREAS.items()}
        return ContractAnalysis(**values)
