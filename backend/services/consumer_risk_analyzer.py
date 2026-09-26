from __future__ import annotations

from collections import defaultdict

from models.analysis_v2 import Ambiguity, Fact, Gap
from models.consumer_risk import ConsumerRiskAnalysis, RiskArea, RiskLevel
from models.enums import FactCategory, Importance
from models.qualification import FactQualification, QualificationDisposition


class ConsumerRiskAnalyzer:
    AREA_ORDER = ("payment", "privacy", "tracking", "retention", "contract", "content", "ai")

    AREA_DEFINITIONS = {
        "payment": ("Payment terms", "Money", "Pricing, recurring charges, trials, fees, refunds, or payment conditions."),
        "privacy": ("Data and privacy", "Data", "Information the service collects, uses, shares, sells, or otherwise receives permission to handle."),
        "tracking": ("Tracking and advertising", "Tracking", "Cookies, tracking technologies, profiling, or advertising-related use of information."),
        "ai": ("AI and model use", "AI", "Use of submitted information or content for AI, machine learning, or model improvement."),
        "contract": ("Contractual commitments", "Agreement", "Arbitration, liability, termination, governing law, licenses, and other contractual conditions."),
        "content": ("Content permissions", "Content", "Rights or permissions granted over material the user submits or uploads."),
        "retention": ("Data retention and deletion", "Retention", "How long information is kept and whether deletion is described."),
    }

    CATEGORY_TO_AREA = {
        FactCategory.SUBSCRIPTION: "payment",
        FactCategory.AUTO_RENEWAL: "payment",
        FactCategory.TRIAL: "payment",
        FactCategory.FEE: "payment",
        FactCategory.REFUND: "payment",
        FactCategory.CANCELLATION: "payment",
        FactCategory.DATA_COLLECTION: "privacy",
        FactCategory.DATA_SHARING: "privacy",
        FactCategory.DATA_USAGE: "privacy",
        FactCategory.TRACKING: "tracking",
        FactCategory.ADVERTISING: "tracking",
        FactCategory.AI_USAGE: "ai",
        FactCategory.RETENTION: "retention",
        FactCategory.DELETION: "retention",
        FactCategory.ARBITRATION: "contract",
        FactCategory.LIABILITY: "contract",
        FactCategory.TERMINATION: "contract",
        FactCategory.CONTENT_LICENSE: "content",
        FactCategory.GOVERNING_LAW: "contract",
    }

    def _level(self, qualification: FactQualification | None) -> RiskLevel:
        if qualification is None:
            return RiskLevel.LOW
        if qualification.importance == Importance.HIGH:
            return RiskLevel.HIGH
        if qualification.importance == Importance.MEDIUM:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    @staticmethod
    def _title(area: str, facts: list[Fact]) -> str:
        if area == "payment" and any(f.category == FactCategory.AUTO_RENEWAL for f in facts):
            return "Recurring payment condition"
        if area == "privacy" and any(f.category == FactCategory.DATA_SHARING for f in facts):
            return "Information sharing"
        if area == "tracking":
            return "Tracking or advertising use"
        if area == "ai":
            return "AI or model use"
        if area == "contract" and any(f.category == FactCategory.ARBITRATION for f in facts):
            return "Dispute resolution term"
        if area == "content":
            return "Content permission"
        if area == "retention":
            return "Retention or deletion"
        return ConsumerRiskAnalyzer.AREA_DEFINITIONS[area][0]

    @staticmethod
    def _summary(area: str, facts: list[Fact], ambiguities: list[Ambiguity]) -> str:
        if facts:
            return facts[0].object_[:420]
        if ambiguities:
            return ambiguities[0].text[:420]
        return ConsumerRiskAnalyzer.AREA_DEFINITIONS[area][2]

    @staticmethod
    def _why(area: str, level: RiskLevel) -> str:
        base = ConsumerRiskAnalyzer.AREA_DEFINITIONS[area][2]
        if level == RiskLevel.HIGH:
            return f"This area contains a condition that may have a meaningful effect on the user's {ConsumerRiskAnalyzer.AREA_DEFINITIONS[area][1].lower()} or contractual position."
        if level == RiskLevel.MODERATE:
            return f"This area contains a term worth understanding because it can affect the user's {ConsumerRiskAnalyzer.AREA_DEFINITIONS[area][1].lower()} or choices."
        return base

    def analyze(
        self,
        facts: list[Fact],
        qualifications: list[FactQualification],
        gaps: list[Gap],
        ambiguities: list[Ambiguity],
        is_consumer_document: bool = True,
    ) -> ConsumerRiskAnalysis:
        if not is_consumer_document:
            return ConsumerRiskAnalysis(
                overall_level=RiskLevel.NOT_APPLICABLE,
                title="Customer risk assessment not applicable",
                explanation="The supplied content does not appear to be a customer-facing purchase, account, permission, tracking, content-rights, or contractual document that can be assessed from a customer perspective.",
            )
        qmap = {q.fact_id: q for q in qualifications}
        facts_by_area: dict[str, list[Fact]] = defaultdict(list)
        for fact in facts:
            if fact.category in self.CATEGORY_TO_AREA:
                facts_by_area[self.CATEGORY_TO_AREA[fact.category]].append(fact)

        areas: list[RiskArea] = []
        overall = RiskLevel.LOW
        for area, area_facts in facts_by_area.items():
            surfaced = [f for f in area_facts if qmap.get(f.fact_id) and qmap[f.fact_id].should_surface]
            if surfaced:
                levels = [self._level(qmap[f.fact_id]) for f in surfaced]
                if RiskLevel.HIGH in levels:
                    level = RiskLevel.HIGH
                elif RiskLevel.MODERATE in levels:
                    level = RiskLevel.MODERATE
                else:
                    level = RiskLevel.LOW
                if level == RiskLevel.HIGH:
                    overall = RiskLevel.HIGH
                elif level == RiskLevel.MODERATE and overall != RiskLevel.HIGH:
                    overall = RiskLevel.MODERATE
                area_evidence = [eid for fact in surfaced for eid in fact.evidence_ids]
                areas.append(RiskArea(
                    area=area,
                    level=level,
                    title=self._title(area, surfaced),
                    summary=self._summary(area, surfaced, []),
                    why_it_matters=self._why(area, level),
                    evidence_ids=area_evidence,
                ))

        for gap in gaps:
            area = "payment" if gap.category in {"cancellation process", "refund terms"} else "retention" if gap.category == "retention period" else "privacy"
            if any(item.area == area for item in areas):
                continue
            level = RiskLevel.MODERATE if gap.importance == Importance.MEDIUM else RiskLevel.LOW
            if level == RiskLevel.MODERATE and overall == RiskLevel.LOW:
                overall = RiskLevel.MODERATE
            areas.append(RiskArea(
                area=area,
                level=level,
                title="Missing information",
                summary=gap.description,
                why_it_matters="An important detail was not clearly found in the supplied document.",
                evidence_ids=gap.evidence,
            ))

        if not areas and is_consumer_document:
            overall = RiskLevel.LOW
            title = "No significant customer-facing risk identified"
            explanation = "The document contains customer-facing terms, but the qualifying checks did not identify a higher-attention condition for a customer."
        elif not areas:
            overall = RiskLevel.NOT_APPLICABLE
            title = "Customer risk assessment not applicable"
            explanation = "The supplied content does not appear to be a customer-facing purchase, account, permission, tracking, content-rights, or contractual document that can be assessed from a customer perspective."
        elif overall == RiskLevel.HIGH:
            title = "Several customer-facing terms deserve close review"
            explanation = "The document contains one or more conditions that may have a meaningful impact on a customer based on the supplied wording and evidence."
        elif overall == RiskLevel.MODERATE:
            title = "A few customer-facing areas deserve attention"
            explanation = "The document contains terms that may affect a customer’s payment, permissions, privacy, or contractual choices and are worth understanding before proceeding."
        else:
            title = "No significant customer-facing risk identified"
            explanation = "The analysis found relevant customer-facing terms, but none met the threshold for a higher attention level."
        level_rank = {RiskLevel.HIGH: 0, RiskLevel.MODERATE: 1, RiskLevel.LOW: 2, RiskLevel.NOT_APPLICABLE: 3}
        area_rank = {area: index for index, area in enumerate(self.AREA_ORDER)}
        areas.sort(key=lambda item: (level_rank.get(item.level, 9), area_rank.get(item.area, 99), item.title.lower()))

        return ConsumerRiskAnalysis(
            overall_level=overall,
            title=title,
            explanation=explanation,
            areas=areas[:12],
        )
