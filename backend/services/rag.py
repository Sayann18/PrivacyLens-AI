from services.evidence import Evidence


def build_explanation(claim: str, evidence: list[Evidence], verdict: str) -> str:
    if not evidence:
        return "No configured evidence provider returned sufficiently relevant sources. This claim needs manual verification."
    support = sum(item.stance == "supports" for item in evidence)
    refute = sum(item.stance == "refutes" for item in evidence)
    return (
        f"The claim was assessed against {len(evidence)} relevant sources. "
        f"{support} source(s) appear to support it and {refute} appear to refute it; "
        f"the current evidence-based verdict is {verdict.lower()}."
    )
