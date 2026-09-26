from services.evidence import Evidence


def score_verdict(evidence: list[Evidence]) -> tuple[str, float]:
    if not evidence:
        return "INSUFFICIENT_EVIDENCE", 0.0
    support = sum(item.relevance for item in evidence if item.stance == "supports")
    refute = sum(item.relevance for item in evidence if item.stance == "refutes")
    coverage = min(len(evidence) / 5, 1.0)
    if support == 0 and refute == 0:
        return "INSUFFICIENT_EVIDENCE", round(0.2 * coverage, 2)
    total = support + refute
    winner, loser, verdict = (support, refute, "LIKELY_TRUE") if support >= refute else (refute, support, "LIKELY_FALSE")
    confidence = min(0.95, 0.35 + 0.45 * (winner / total) + 0.2 * coverage)
    if abs(support - refute) / total < 0.2:
        verdict = "MIXED_EVIDENCE"
    return verdict, round(confidence, 2)
