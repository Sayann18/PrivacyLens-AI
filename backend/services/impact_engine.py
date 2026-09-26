from __future__ import annotations

from dataclasses import dataclass, replace

from models.analysis_v2 import Ambiguity, ContractAnalysis, Fact, Gap, PrivacyAnalysis, FinancialAnalysis
from models.qualification import FactQualification, QualificationDisposition
from models.enums import Confidence, FactCategory, Importance


@dataclass(frozen=True)
class ImpactedFinding:
    title: str
    category: str
    importance: Importance
    confidence: Confidence
    summary: str
    why_it_matters: str
    evidence_ids: list[str]
    impact: float


class ImpactEngine:
    CATEGORY_WEIGHT = {
        FactCategory.DATA_SHARING: 0.9,
        FactCategory.AI_USAGE: 0.9,
        FactCategory.AUTO_RENEWAL: 0.85,
        FactCategory.ARBITRATION: 0.85,
        FactCategory.LIABILITY: 0.85,
        FactCategory.CONTENT_LICENSE: 0.75,
        FactCategory.CANCELLATION: 0.7,
        FactCategory.RETENTION: 0.7,
        FactCategory.TRACKING: 0.65,
        FactCategory.ADVERTISING: 0.6,
        FactCategory.DELETION: 0.55,
        FactCategory.FEE: 0.65,
        FactCategory.REFUND: 0.65,
        FactCategory.TERMINATION: 0.7,
    }

    def _importance(self, score: float) -> Importance:
        if score >= 0.78:
            return Importance.HIGH
        if score >= 0.5:
            return Importance.MEDIUM
        return Importance.LOW

    def score_facts(self, facts: list[Fact]) -> list[ImpactedFinding]:
        findings = []
        for fact in facts:
            base = self.CATEGORY_WEIGHT.get(fact.category, 0.4)
            confidence = max(0.0, min(1.0, fact.confidence))
            score = base * (0.55 + 0.45 * confidence)
            importance = self._importance(score)
            findings.append(ImpactedFinding(
                title=fact.category.value.replace("_", " ").title(),
                category=fact.category.value,
                importance=importance,
                confidence=Confidence.HIGH if confidence >= 0.85 else Confidence.MEDIUM if confidence >= 0.6 else Confidence.LOW,
                summary=fact.object_[:240],
                why_it_matters="This clause may affect your privacy, money, contractual rights, or use of the service depending on its scope and conditions.",
                evidence_ids=fact.evidence_ids,
                impact=score,
            ))
        return findings

    def score_gaps(self, gaps: list[Gap]) -> list[ImpactedFinding]:
        return [ImpactedFinding(g.category, g.category, g.importance, g.confidence, g.description, "This information was not clearly found in the supplied document.", g.evidence, 0.55 if g.importance == Importance.MEDIUM else 0.35) for g in gaps]

    def score_ambiguities(self, ambiguities: list[Ambiguity]) -> list[ImpactedFinding]:
        return [ImpactedFinding(a.category.replace("_", " ").title(), a.category, a.importance, a.confidence, a.text[:240], a.explanation, a.evidence, 0.52) for a in ambiguities]

    async def score(
        self,
        facts: list[Fact],
        gaps: list[Gap],
        ambiguities: list[Ambiguity],
        qualifications: list[FactQualification] | None = None,
    ) -> list[ImpactedFinding]:
        if qualifications is None:
            fact_findings = self.score_facts(facts)
        else:
            qualification_by_id = {q.fact_id: q for q in qualifications}
            qualified_facts = [
                fact
                for fact in facts
                if qualification_by_id.get(fact.fact_id)
                and qualification_by_id[fact.fact_id].should_surface
                and qualification_by_id[fact.fact_id].disposition in {
                    QualificationDisposition.ATTENTION,
                    QualificationDisposition.AMBIGUOUS,
                    QualificationDisposition.CONFLICTING,
                }
            ]
            raw_findings = self.score_facts(qualified_facts)
            fact_findings = []
            for fact, finding in zip(qualified_facts, raw_findings):
                q = qualification_by_id[fact.fact_id]
                fact_findings.append(replace(finding, importance=q.importance, confidence=q.confidence))
        all_findings = fact_findings + self.score_gaps(gaps) + self.score_ambiguities(ambiguities)
        
        
        
        unique: list[ImpactedFinding] = []
        seen: set[tuple[str, tuple[str, ...], str]] = set()
        for finding in all_findings:
            key = (finding.category, tuple(finding.evidence_ids), finding.summary.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique
