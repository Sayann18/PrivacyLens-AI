from __future__ import annotations

import re
from typing import Iterable
from uuid import uuid4

from models.analysis_v2 import Evidence
from models.enums import EvidenceStrength, Confidence


class EvidenceService:

    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}

    @staticmethod
    def _normalize_quote(quote: str) -> str:
        return re.sub(r"\s+", " ", quote.strip())

    @staticmethod
    def _confidence(value: float | Confidence) -> float:
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        return {Confidence.LOW: 0.4, Confidence.MEDIUM: 0.7, Confidence.HIGH: 0.95}[value]

    def create_evidence(
        self,
        source_document: str,
        exact_quote: str,
        evidence_type: EvidenceStrength = EvidenceStrength.DIRECT,
        confidence: float | Confidence = 1.0,
        *,
        source_url: str | None = None,
        page: int | None = None,
        section: str | None = None,
    ) -> Evidence:
        quote = exact_quote.strip()
        evidence = Evidence(
            evidence_id=str(uuid4()),
            source_document=source_document,
            source_url=source_url,
            page=page,
            section=section,
            exact_quote=quote,
            normalized_quote=self._normalize_quote(quote),
            evidence_type=evidence_type,
            confidence=self._confidence(confidence),
        )
        self._items[evidence.evidence_id] = evidence
        return evidence

    def get_by_id(self, evidence_id: str) -> Evidence | None:
        return self._items.get(evidence_id)

    def get_by_section(self, section: str) -> list[Evidence]:
        return [item for item in self._items.values() if item.section == section]

    def get_all(self) -> list[Evidence]:
        return list(self._items.values())

    def extend(self, items: Iterable[Evidence]) -> None:
        for item in items:
            self._items[item.evidence_id] = item
