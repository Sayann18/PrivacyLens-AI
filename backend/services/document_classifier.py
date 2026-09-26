from __future__ import annotations

import re
from dataclasses import dataclass

from models.enums import DocumentType
from models.normalized_document import NormalizedDocument


@dataclass(frozen=True)
class ClassificationResult:
    primary_type: DocumentType
    secondary_types: list[DocumentType]
    confidence: float
    is_consumer_document: bool = False


class DocumentClassifier:
    PATTERNS = {
        DocumentType.PRIVACY_POLICY: [r"\bprivacy policy\b", r"\bdata we collect\b", r"\bpersonal information we collect\b"],
        DocumentType.COOKIE_POLICY: [r"\bcookie policy\b", r"\bcookies and similar technologies\b", r"\bweb beacons\b"],
        DocumentType.TERMS_OF_SERVICE: [r"\bterms of service\b", r"\bterms of use\b"],
        DocumentType.TERMS_AND_CONDITIONS: [r"\bterms\s*(?:and|&)\s*conditions\b", r"\bconditions of use\b", r"\bbank(?:ing)?\s+terms\b"],
        DocumentType.SUBSCRIPTION_TERMS: [r"\bsubscription terms?\b", r"\bautomatic(?:ally)? renew(?:al|s)?\b", r"\brecurring billing\b", r"\btrial period\b"],
        DocumentType.REFUND_POLICY: [r"\brefund policy\b", r"\brefunds?\b", r"\bmoney back\b"],
        DocumentType.EULA: [r"\bend user license agreement\b", r"\beula\b"],
        DocumentType.SERVICE_AGREEMENT: [r"\bservice agreement\b", r"\bmaster services agreement\b", r"\bmsa\b"],
        DocumentType.DATA_PROCESSING_AGREEMENT: [r"\bdata processing agreement\b", r"\bdpa\b"],
    }

    TECHNICAL_SIGNALS = (
        "implementation plan", "backend", "frontend", "api/", "pytest", "test files", "test suite",
        "pydantic", "fastapi", "uvicorn", "router", "endpoint", "python", "typescript", "javascript",
        "requirements.txt", "source code", "developer", "task ", "class ", "function ", "pytest.ini",
        "implementation", "architecture", "repository", "dependency", "unit test", "code"
    )

    STRONG_HEADLINE_PATTERNS = (
        r"\bprivacy policy\b", r"\bterms of service\b", r"\bterms of use\b", r"\bterms and conditions\b",
        r"\bsubscription terms?\b", r"\bcookie policy\b", r"\brefund policy\b", r"\bend user license agreement\b",
        r"\bservice agreement\b", r"\bdata processing agreement\b",
    )

    STRONG_CONSUMER_SIGNALS = (
        "privacy policy", "terms of service", "terms and conditions", "terms & conditions", "subscription terms", "refund policy",
        "cookie policy", "end user license agreement", "service agreement", "data processing agreement",
        "billing", "subscription", "renewal", "trial", "refund", "payment", "personal information", "personal data", "collect your", "share your", "sell your", "retain your", "use your data", "cookies"
    )

    def classify(self, document: NormalizedDocument) -> ClassificationResult:
        text = document.raw_text.lower()
        if not text:
            return ClassificationResult(DocumentType.UNKNOWN, [], 0.0)

        technical_count = sum(text.count(signal) for signal in self.TECHNICAL_SIGNALS)
        consumer_anchor_count = sum(text.count(signal) for signal in self.STRONG_CONSUMER_SIGNALS)
        scores: dict[DocumentType, float] = {kind: 0.0 for kind in self.PATTERNS}
        for kind, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.I))
                scores[kind] += min(matches, 4) * 0.25

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if not ranked or ranked[0][1] == 0:
            return ClassificationResult(DocumentType.UNKNOWN, [], 0.2, consumer_anchor_count > 0 and technical_count < 4)

        primary, raw = ranked[0]
        headline_text = text[:400]
        strong_headline = any(re.search(pattern, headline_text, re.I) for pattern in self.STRONG_HEADLINE_PATTERNS)
        consumer_document = strong_headline or (consumer_anchor_count > 0 and technical_count < 4)
        if technical_count >= 6 and not strong_headline:
            return ClassificationResult(DocumentType.UNKNOWN, [], 0.35, False)
        if technical_count >= 4 and not consumer_document:
            return ClassificationResult(DocumentType.UNKNOWN, [], 0.3, False)

        confidence = min(0.98, 0.45 + raw / 2.0)
        secondary = [kind for kind, score in ranked[1:3] if score >= max(0.35, raw * 0.5)]
        if DocumentType.PRIVACY_POLICY in {primary, *secondary} and any(
            kind in {DocumentType.TERMS_OF_SERVICE, DocumentType.TERMS_AND_CONDITIONS} for kind in {primary, *secondary}
        ):
            return ClassificationResult(primary, secondary, max(confidence, 0.9), consumer_document)
        return ClassificationResult(primary, secondary, confidence, consumer_document)
