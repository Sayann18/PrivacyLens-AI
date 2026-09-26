from __future__ import annotations

import re
from models.analysis_v2 import Ambiguity, Evidence
from models.enums import Confidence, Importance
from models.normalized_document import NormalizedDocument
from services.evidence_service import EvidenceService


class AmbiguityAnalyzer:
    PATTERNS = (
        (r"\bas necessary\b", "necessity wording"),
        (r"\bfrom time to time\b", "change frequency"),
        (r"\bcertain partners\b", "unspecified partners"),
        (r"\bat our discretion\b", "discretionary authority"),
        (r"\bmay include\b", "open-ended scope"),
        (r"\bas permitted by law\b", "legal qualifier"),
    )

    async def analyze(self, document: NormalizedDocument, evidence_service: EvidenceService) -> list[Ambiguity]:
        result: list[Ambiguity] = []
        for pattern, category in self.PATTERNS:
            match = re.search(rf"[^.!?\n]*{pattern}[^.!?\n]*[.!?]?", document.raw_text, re.I)
            if not match:
                continue
            quote = match.group(0).strip()
            ev = evidence_service.create_evidence(document.source_name, quote, confidence=0.75, source_url=document.source_url)
            result.append(Ambiguity(
                text=quote, category=category,
                explanation="The wording leaves scope, timing, or conditions less specific than a fully defined clause.",
                importance=Importance.MEDIUM, evidence=[ev.evidence_id], confidence=Confidence.MEDIUM,
            ))
        return result
