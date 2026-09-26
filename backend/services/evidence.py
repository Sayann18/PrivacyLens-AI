from dataclasses import dataclass
import re


@dataclass
class Evidence:
    title: str
    url: str
    snippet: str
    source: str
    published_at: str | None = None
    relevance: float = 0.0
    stance: str = "neutral"


def claim_terms(claim: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]{3,}", claim.lower())}


def estimate_relevance(claim: str, evidence: Evidence) -> float:
    terms = claim_terms(claim)
    candidate = set(re.findall(r"[a-zA-Z0-9]{3,}", f"{evidence.title} {evidence.snippet}".lower()))
    return round(len(terms & candidate) / max(len(terms), 1), 3)


def infer_stance(claim: str, evidence: Evidence) -> str:
    text = f"{evidence.title} {evidence.snippet}".lower()
    negative = ("false", "incorrect", "misleading", "debunk", "no evidence", "not true", "hoax")
    positive = ("confirmed", "true", "accurate", "supports", "evidence shows", "verified")
    if any(phrase in text for phrase in negative):
        return "refutes"
    if any(phrase in text for phrase in positive):
        return "supports"
    return "neutral"
