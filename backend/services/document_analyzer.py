from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from models.analysis import DocumentAnalysisResponse, Finding, Location, Section
from services.cache import TTLCache
from utils.config import get_settings

ANALYSIS_VERSION = "1.0.1"
SECTION_NAMES = ("Privacy", "Data Collection", "Information Sharing", "Cookies", "Account", "Payments", "Subscription", "Cancellation", "Refunds", "Termination", "Intellectual Property", "User Content", "Liability", "Indemnification", "Dispute Resolution", "Arbitration", "Governing Law", "Changes to Terms", "Security")
RULES = (
    ("data_sharing", "Data sharing", "high", r"\b(share|disclose|provide).{0,100}\b(affiliate|partner|third part|advertis|service provider)"),
    ("data_sale", "Data sale", "high", r"\b(sell|sale of).{0,100}\b(personal information|personal data|data)"),
    ("tracking_advertising", "Tracking and advertising", "medium", r"\b(track|targeted advertis|advertising partner|behavioral advertis)"),
    ("cookies", "Cookies", "low", r"\b(cookie|web beacon|pixel)"),
    ("data_retention", "Data retention", "medium", r"\b(retain|retention|keep).{0,100}\b(data|information)"),
    ("data_deletion", "Data deletion", "medium", r"\b(delete|deletion|erase).{0,100}\b(data|information|account)"),
    ("ai_data_training", "AI or data training", "high", r"\b(train|training|improve).{0,100}\b(model|artificial intelligence|AI)\b"),
    ("account_termination", "Account termination", "medium", r"\b(terminate|suspend|disable).{0,100}\b(account|access|service)"),
    ("payment", "Payment obligations", "medium", r"\b(payment|fees?|charges?|billing)\b"),
    ("auto_renewal", "Automatic renewal", "high", r"\b(auto(?:matic)?(?:ally)? renew|renewal|recurring charge)"),
    ("cancellation", "Cancellation restrictions", "medium", r"\b(cancel|cancellation).{0,100}\b(subscription|service|account)"),
    ("refunds", "Refund limitations", "medium", r"\b(no refund|non-refundable|refund)"),
    ("liability", "Liability limitation", "high", r"\b(limit(?:ation)? of liability|not liable|no liability)"),
    ("indemnification", "Indemnification", "high", r"\b(indemnif|hold harmless)"),
    ("arbitration", "Mandatory arbitration", "high", r"\b(binding arbitration|arbitrat)"),
    ("class_action_waiver", "Class action waiver", "high", r"\b(class action|class[- ]wide)"),
    ("governing_law", "Governing law", "info", r"\b(governed by|governing law|laws of)"),
    ("ownership", "Content ownership", "medium", r"\b(own|ownership).{0,100}\b(content|material|submission)"),
    ("license_grant", "License grant", "high", r"\b(license|licence).{0,100}\b(content|submission|user content)"),
    ("terms_changes", "Changes to terms", "low", r"\b(modify|change|update).{0,100}\b(these terms|terms of service|agreement)"),
)


class DocumentAnalyzer:
    def __init__(self) -> None:
        self.cache = TTLCache(get_settings().cache_ttl_seconds)

    def analyze(self, source: str, text: str) -> DocumentAnalysisResponse:
        normalized = self._normalize(text)
        key = hashlib.sha256(f"{ANALYSIS_VERSION}:{normalized}".encode()).hexdigest()
        if cached := self.cache.get(key):
            return cached.model_copy(update={"source": source, "cached": True})
        document_type, confidence = self._classify(normalized)
        sections = self._sections(normalized)
        findings = self._findings(normalized, sections)
        score = min(100, sum({"high": 18, "medium": 9, "low": 3, "info": 0}[finding.severity] for finding in findings))
        level = "High" if score >= 55 else "Moderate" if score >= 25 else "Low"
        summary = self._summary(document_type, findings, score)
        response = DocumentAnalysisResponse(source=source, document_type=document_type, classification_confidence=confidence, sections=sections, findings=findings, top_things_to_know=[finding.title + ": " + finding.explanation for finding in findings[:5]], overall_risk_score=score, overall_risk_level=level, summary=summary, analysis_version=ANALYSIS_VERSION)
        self.cache.set(key, response)
        return response

    async def analyze_async(self, source: str, text: str) -> DocumentAnalysisResponse:
        response = self.analyze(source, text)
        try:
            from services.openai_provider import is_configured, structured_json

            if not is_configured() or not response.findings:
                return response
            findings_brief = "\n".join(f"- [{finding.severity}] {finding.title}: {finding.clause[:200]}" for finding in response.findings[:20])
            ai_result = await structured_json(
                system_prompt=(
                    "You write a short, plain-language summary of a legal document's already-"
                    "identified risk findings for a non-lawyer reader. Do not add new findings, "
                    "clauses, or claims beyond what is listed."
                ),
                user_content=f"Document type: {response.document_type}\nRisk score: {response.overall_risk_score}/100\nFindings:\n{findings_brief}",
                schema_hint='{"summary": "string, 2-4 sentences"}',
            )
            if ai_result and isinstance(ai_result.get("summary"), str) and ai_result["summary"].strip():
                return response.model_copy(update={"summary": ai_result["summary"].strip()})
        except Exception:  
            pass
        return response

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[ \t]+", " ", re.sub(r"\r\n?", "\n", text)).strip()

    @staticmethod
    def _classify(text: str) -> tuple[str, float]:
        value = text.lower()
        privacy = sum(term in value for term in ("privacy policy", "personal information", "personal data", "cookies"))
        terms = sum(term in value for term in ("terms of service", "terms and conditions", "governing law", "limitation of liability"))
        subscription = sum(term in value for term in ("subscription", "automatic renewal", "billing", "refund"))
        if privacy and terms: return "mixed_terms_privacy", 0.9
        if privacy >= 2: return "privacy_policy", 0.88
        if terms >= 2: return "terms_and_conditions", 0.88
        if subscription >= 2: return "subscription_terms", 0.78
        if len(text) > 250 and (privacy or terms or subscription): return "service_agreement", 0.58
        return "unknown", 0.2

    @staticmethod
    def _sections(text: str) -> list[Section]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        headings = [(index, line) for index, line in enumerate(lines) if line.lower().rstrip(":") in {name.lower() for name in SECTION_NAMES} or (len(line) < 70 and re.match(r"^\d+(?:\.\d+)*[.)]?\s+", line))]
        if not headings: return [Section(title="Document", text=text[:12000])]
        sections = []
        for position, (start, title) in enumerate(headings):
            end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
            sections.append(Section(title=title[:120], text="\n".join(lines[start:end])[:12000]))
        return sections[:80]

    def _findings(self, text: str, sections: list[Section]) -> list[Finding]:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        seen, findings = set(), []
        for category, title, severity, pattern in RULES:
            match_sentence = next((sentence.strip() for sentence in sentences if re.search(pattern, sentence, re.I)), None)
            if not match_sentence or category in seen:
                continue
            seen.add(category)
            section = next((item.title for item in sections if match_sentence[:40] in item.text), "Document")
            plain = self._plain_english(category)
            findings.append(Finding(category=category, severity=severity, title=title, clause=match_sentence[:1000], explanation=plain, why_it_matters=self._why(severity), recommendation="Review this clause and decide whether its scope is acceptable before agreeing.", confidence=0.9, evidence_quality="strong", location=Location(section=section)))
        return sorted(findings, key=lambda item: {"high": 0, "medium": 1, "low": 2, "info": 3}[item.severity])

    @staticmethod
    def _plain_english(category: str) -> str:
        return {"data_sharing": "The document permits sharing information with other organizations.", "auto_renewal": "The service may continue charging unless you cancel under its stated process.", "liability": "The company limits what it may owe if something goes wrong.", "arbitration": "Disputes may need to be resolved through arbitration instead of court.", "license_grant": "The company receives a licence to use content you provide."}.get(category, "This clause describes a condition that may affect your privacy, money, or legal rights.")

    @staticmethod
    def _why(severity: str) -> str:
        return {"high": "This can materially affect your privacy, money, ownership, or ability to resolve disputes.", "medium": "This is an important restriction or obligation to understand.", "low": "This is a common provision but is still worth reviewing.", "info": "This is standard context that may be useful."}[severity]

    @staticmethod
    def _summary(document_type: str, findings: list[Finding], score: int) -> str:
        if document_type == "unknown":
            return "Detected a general document. Analysis is based only on supported privacy, data-use, payment, tracking, liability, and related clauses."
        return f"Detected {document_type.replace('_', ' ')} with {len(findings)} evidence-grounded findings and an overall risk score of {score}/100."
