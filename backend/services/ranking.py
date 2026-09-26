from services.evidence import Evidence, estimate_relevance, infer_stance


def rank_evidence(claim: str, items: list[Evidence], limit: int) -> list[Evidence]:
    unique: dict[str, Evidence] = {}
    for item in items:
        if not item.url or item.url in unique:
            continue
        item.relevance = estimate_relevance(claim, item)
        item.stance = infer_stance(claim, item)
        unique[item.url] = item
    return sorted(unique.values(), key=lambda item: item.relevance, reverse=True)[:limit]
