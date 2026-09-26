from __future__ import annotations

from models.analysis_v2 import Fact, Gap
from models.enums import Confidence, FactCategory, Importance
from models.normalized_document import NormalizedDocument


class GapAnalyzer:
    REQUIRED_AREAS = (
        (FactCategory.RETENTION, "retention period", "The document does not clearly state how long covered information is retained."),
        (FactCategory.DATA_SHARING, "third-party categories", "The document does not clearly identify the categories of third parties receiving data."),
        (FactCategory.CANCELLATION, "cancellation process", "The document does not clearly state the practical steps required to cancel."),
        (FactCategory.REFUND, "refund terms", "The document does not clearly state a refund rule."),
    )

    async def analyze(self, document: NormalizedDocument, facts: list[Fact]) -> list[Gap]:
        categories = {fact.category for fact in facts}
        if len(document.raw_text.split()) < 30:
            return []
        lower = document.raw_text.lower()
        privacy_signals = ("privacy", "personal data", "personal information", "we collect", "cookies", "data sharing")
        financial_signals = ("subscription", "billing", "payment", "price", "refund", "trial", "renew", "charge")
        gaps: list[Gap] = []
        for category, label, description in self.REQUIRED_AREAS:
            if category in categories:
                continue
            if label in {"retention period", "third-party categories"} and not any(s in lower for s in privacy_signals):
                continue
            if label in {"cancellation process", "refund terms"} and not any(s in lower for s in financial_signals):
                continue
            gaps.append(Gap(category=label, description=description, importance=Importance.MEDIUM, evidence=[], confidence=Confidence.MEDIUM))
        return gaps
