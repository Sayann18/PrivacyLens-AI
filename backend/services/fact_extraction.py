from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from models.analysis_v2 import Fact, DocumentSection, Evidence
from models.enums import FactCategory, DisclosureStatus, EvidenceStrength
from models.normalized_document import NormalizedDocument
from services.evidence_service import EvidenceService
from services.llm_provider import LLMProvider, get_llm_provider
from utils.config import get_settings


@dataclass(frozen=True)
class FactExtractionResult:
    facts: list[Fact]
    evidence: list[Evidence]
    warnings: list[str]
    used_llm: bool = False


class FactExtractionService:
    RULES = (
        (FactCategory.DATA_COLLECTION, r"(?:collect|gather|receive|obtain|store)\b.{0,180}\b(?:personal|information|data|email|name|address|identifier)") ,
        (FactCategory.DATA_SHARING, r"\b(?:share|disclose|provide|transfer)\b.{0,180}\b(?:third part|affiliate|partner|service provider|vendor|contractor)") ,
        (FactCategory.DATA_USAGE, r"\b(?:use|process)\b.{0,180}\b(?:data|information)\b.{0,120}\b(?:provide|improve|operate|personalize|service|security)") ,
        (FactCategory.TRACKING, r"\b(?:cookie|tracking|web beacon|pixel|analytics)\w*\b") ,
        (FactCategory.ADVERTISING, r"\b(?:advertis|marketing|targeted ads?|ad network|promotional)\w*\b") ,
        (FactCategory.AI_USAGE, r"\b(?:train|training|improve|artificial intelligence|machine learning|AI model)\b.{0,160}\b(?:data|information|model|service)?") ,
        (FactCategory.RETENTION, r"\b(?:retain|retention|keep)\b.{0,160}\b(?:data|information|records?|account)") ,
        (FactCategory.DELETION, r"\b(?:delete|deletion|erase|remove)\b.{0,160}\b(?:data|information|account)") ,
        (FactCategory.SUBSCRIPTION, r"\bsubscription\b.{0,160}\b(?:plan|service|fee|billing|term)") ,
        (FactCategory.AUTO_RENEWAL, r"\b(?:automatically renew|auto-renew|renewal|recurring)\w*\b.{0,120}\b(?:charge|fee|subscription|billing|payment)?") ,
        (FactCategory.TRIAL, r"\b(?:free trial|trial period|trial)\b") ,
        (FactCategory.FEE, r"\b(?:fee|fees|charge|charges|price|pricing|billing)\b") ,
        (FactCategory.REFUND, r"\b(?:refund|refundable|non-refundable|money back)\w*\b") ,
        (FactCategory.CANCELLATION, r"\b(?:cancel|cancellation)\w*\b.{0,160}\b(?:subscription|service|account|plan)") ,
        (FactCategory.ARBITRATION, r"\b(?:binding )?arbitration\b") ,
        (FactCategory.LIABILITY, r"\b(?:limitation of liability|not liable|no liability|liability)\b") ,
        (FactCategory.TERMINATION, r"\b(?:terminate|termination|suspend|suspension|disable)\w*\b.{0,140}\b(?:account|service|access|agreement)") ,
        (FactCategory.CONTENT_LICENSE, r"\b(?:license|licence)\b.{0,180}\b(?:content|materials|user content|use)") ,
        (FactCategory.GOVERNING_LAW, r"\b(?:governed by|governing law|laws of|jurisdiction)\b") ,
    )

    def __init__(self, provider: LLMProvider | None = None, evidence_service: EvidenceService | None = None, use_llm: bool = True) -> None:
        self.provider = provider or get_llm_provider()
        self.evidence = evidence_service or EvidenceService()
        self.use_llm = use_llm

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]

    @staticmethod
    def _subject(category: FactCategory) -> str:
        return {FactCategory.DATA_COLLECTION: "company", FactCategory.DATA_SHARING: "company", FactCategory.TRACKING: "service", FactCategory.AUTO_RENEWAL: "subscription", FactCategory.CANCELLATION: "user", FactCategory.REFUND: "company"}.get(category, "document subject")

    @staticmethod
    def _usable_sentence(sentence: str) -> bool:
        words = sentence.split()
        if len(words) >= 4:
            return True
        return bool(re.search(r"\b(?:we|you|your|our|may|will|must|can|is|are|applies|costs|charged|renews|collect|share|retain|delete|use|grant|agree)\b", sentence, re.I))

    def _deterministic(self, document: NormalizedDocument, sections: list[DocumentSection]) -> tuple[list[Fact], list[Evidence]]:
        facts: list[Fact] = []
        evidence_items: list[Evidence] = []
        sentences = self._sentences(document.raw_text)
        seen: set[tuple[FactCategory, str]] = set()
        for category, pattern in self.RULES:
            for sentence in sentences:
                if not self._usable_sentence(sentence):
                    continue
                match = re.search(pattern, sentence, re.I)
                if not match:
                    continue
                key = (category, sentence[:200].lower())
                if key in seen:
                    continue
                seen.add(key)
                section = next((s for s in sections if sentence in s.text or sentence[:40] in s.text), None)
                evidence = self.evidence.create_evidence(
                    document.source_name,
                    sentence[:1200],
                    EvidenceStrength.DIRECT,
                    0.95,
                    source_url=document.source_url,
                    page=section.page if section else None,
                    section=section.title if section else None,
                )
                evidence_items.append(evidence)
                facts.append(Fact(
                    fact_id=f"fact-{len(facts)+1}-{category.value.lower()}",
                    category=category,
                    subject=self._subject(category),
                    action="states or permits",
                    object_=sentence[:500],
                    status=DisclosureStatus.DISCLOSED,
                    evidence_ids=[evidence.evidence_id],
                    confidence=0.9,
                ))
                break
        return facts, evidence_items

    async def _llm(self, document: NormalizedDocument) -> tuple[list[Fact], list[Evidence]]:
        schema = '{"facts":[{"category":"DATA_COLLECTION","subject":"string","action":"string","object":"string","purpose":"string|null","recipient":"string|null","conditions":"string|null","frequency":"string|null","duration":"string|null","status":"DISCLOSED|PARTIALLY_DISCLOSED|AMBIGUOUS|NOT_FOUND|CONFLICTING","evidence_quote":"exact quote","confidence":0.0}]}'
        payload = await self.provider.extract_facts(document.raw_text, schema)
        if not payload or not isinstance(payload.get("facts"), list):
            return [], []
        facts: list[Fact] = []
        evidence: list[Evidence] = []
        for index, raw in enumerate(payload["facts"], 1):
            if not isinstance(raw, dict) or not raw.get("evidence_quote"):
                continue
            quote = str(raw["evidence_quote"]).strip()
            if quote not in document.raw_text:
                continue
            try:
                category = FactCategory(str(raw.get("category")))
                status = DisclosureStatus(str(raw.get("status", DisclosureStatus.DISCLOSED.value)))
                ev = self.evidence.create_evidence(document.source_name, quote, EvidenceStrength.STRONG, float(raw.get("confidence", 0.8)), source_url=document.source_url)
                evidence.append(ev)
                facts.append(Fact(
                    fact_id=f"llm-fact-{index}-{category.value.lower()}",
                    category=category,
                    subject=str(raw.get("subject", "document subject")),
                    action=str(raw.get("action", "states")),
                    object_=str(raw.get("object", "")),
                    purpose=raw.get("purpose"),
                    recipient=raw.get("recipient"),
                    conditions=raw.get("conditions"),
                    frequency=raw.get("frequency"),
                    duration=raw.get("duration"),
                    status=status,
                    evidence_ids=[ev.evidence_id],
                    confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.8)))),
                ))
            except Exception:
                continue
        return facts, evidence

    async def extract(self, document: NormalizedDocument, sections: list[DocumentSection]) -> FactExtractionResult:
        deterministic_facts, deterministic_evidence = self._deterministic(document, sections)
        warnings: list[str] = []
        facts = deterministic_facts
        evidence = deterministic_evidence
        used_llm = False
        if self.use_llm:
            try:
                llm_facts, llm_evidence = await asyncio.wait_for(self._llm(document), timeout=get_settings().openai_timeout_seconds)
            except asyncio.TimeoutError:
                llm_facts, llm_evidence = [], []
                warnings.append("Structured AI extraction timed out; deterministic extraction was used instead.")
            if llm_facts:
                used_llm = True
                existing_keys = {(f.category, f.object_[:180].lower()) for f in facts}
                for fact, ev in zip(llm_facts, llm_evidence):
                    if (fact.category, fact.object_[:180].lower()) not in existing_keys:
                        facts.append(fact)
                        evidence.append(ev)
            elif not deterministic_facts:
                warnings.append("Structured AI extraction was unavailable; no deterministic facts were found.")
        return FactExtractionResult(facts, evidence, warnings, used_llm)
