from __future__ import annotations

from models.analysis_v2 import Highlight
from models.enums import Importance
from services.impact_engine import ImpactedFinding


class PriorityEngine:
    def select(self, findings: list[ImpactedFinding], limit: int = 5) -> tuple[list[ImpactedFinding], list[ImpactedFinding]]:
        ordered = sorted(findings, key=lambda f: (f.importance.value == Importance.HIGH.value, f.impact), reverse=True)
        return ordered[:max(3, min(limit, 5))], ordered[max(3, min(limit, 5)):]

    def highlights(self, findings: list[ImpactedFinding]) -> list[Highlight]:
        selected, _ = self.select(findings)
        return [Highlight(title=f.title, importance=f.importance, summary=f.summary, why_it_matters="", evidence_id=f.evidence_ids[0] if f.evidence_ids else None, confidence=f.confidence) for f in selected]
