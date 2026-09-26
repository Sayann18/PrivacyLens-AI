from __future__ import annotations

from models.analysis_v2 import FinancialAnalysis, FinancialAreaReport, Fact
from models.enums import FactCategory, FinancialClarity, Confidence
from models.normalized_document import NormalizedDocument


class FinancialAnalyzer:
    AREAS = {
        "subscription": FactCategory.SUBSCRIPTION,
        "automatic_renewal": FactCategory.AUTO_RENEWAL,
        "billing_frequency": FactCategory.FEE,
        "trial_period": FactCategory.TRIAL,
        "trial_conversion": FactCategory.TRIAL,
        "listed_prices": FactCategory.FEE,
        "additional_fees": FactCategory.FEE,
        "cancellation_requirements": FactCategory.CANCELLATION,
        "cancellation_deadline": FactCategory.CANCELLATION,
        "refund_policy": FactCategory.REFUND,
        "refund_exceptions": FactCategory.REFUND,
        "price_changes": FactCategory.FEE,
    }

    TERMS = {
        "billing_frequency": ("monthly", "annual", "yearly", "weekly", "billing period", "billing cycle"),
        "listed_prices": ("$", "€", "£", "price", "per month", "per year"),
        "cancellation_deadline": ("days before", "prior to renewal", "notice", "deadline"),
        "price_changes": ("price may change", "change our prices", "pricing may change"),
        "additional_fees": ("fee", "charge", "tax", "surcharge"),
    }

    def _report(self, name: str, category: FactCategory, facts: list[Fact], text: str) -> FinancialAreaReport:
        matching = [f for f in facts if f.category == category]
        lower = text.lower()
        hit = name in self.TERMS and any(term in lower for term in self.TERMS[name])
        clarity = FinancialClarity.EXPLICIT if matching or hit else FinancialClarity.NOT_CLEARLY_STATED
        if matching and any("may" in (f.object_ or "").lower() or "certain" in (f.object_ or "").lower() for f in matching):
            clarity = FinancialClarity.AMBIGUOUS
        if clarity == FinancialClarity.NOT_CLEARLY_STATED:
            say = "This point was not clearly stated in the supplied document."
        elif clarity == FinancialClarity.AMBIGUOUS:
            say = "The document addresses this point, but the wording leaves material details open or conditional."
        else:
            say = matching[0].object_ if matching else "The document contains a relevant clause for this area."
        ids = [eid for fact in matching for eid in fact.evidence_ids]
        confidence = Confidence.HIGH if matching else (Confidence.MEDIUM if hit else Confidence.LOW)
        check = "Check the exact price, timing, exception, or cancellation step in the cited clause before agreeing." if clarity != FinancialClarity.NOT_CLEARLY_STATED else "Check whether a separate billing or help page supplies this information."
        return FinancialAreaReport(area_name=name, clarity=clarity, what_document_says=say[:1200], why_it_matters="This can affect what you pay or how you can change or cancel the service.", evidence_ids=ids, confidence=confidence, what_to_check=check)

    async def analyze(self, document: NormalizedDocument, facts: list[Fact]) -> FinancialAnalysis:
        return FinancialAnalysis(**{name: self._report(name, category, facts, document.raw_text) for name, category in self.AREAS.items()})
