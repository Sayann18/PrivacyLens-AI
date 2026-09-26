from datetime import datetime, timezone
from hashlib import sha256
from models.request import VerifyRequest
from models.response import EvidenceItem, VerificationResponse
from services.cache import TTLCache
from services.rag import build_explanation
from services.ranking import rank_evidence
from services.scoring import score_verdict
from services.search import SearchService
from utils.config import get_settings


class VerificationService:
    def __init__(self) -> None:
        self.cache = TTLCache(get_settings().cache_ttl_seconds)
        self.search = SearchService()

    async def verify(self, request: VerifyRequest) -> VerificationResponse:
        key = sha256(f"{request.claim.lower().strip()}:{request.max_results}".encode()).hexdigest()
        cached = None if request.force_refresh else self.cache.get(key)
        if cached:
            return cached.model_copy(update={"cached": True})
        raw_evidence, sources_checked = await self.search.search(request.claim, request.max_results)
        evidence = rank_evidence(request.claim, raw_evidence, request.max_results)
        verdict, confidence = score_verdict(evidence)
        response = VerificationResponse(
            claim=request.claim,
            verdict=verdict,
            confidence=confidence,
            explanation=build_explanation(request.claim, evidence, verdict),
            evidence=[EvidenceItem(**item.__dict__) for item in evidence],
            sources_checked=sources_checked,
            generated_at=datetime.now(timezone.utc),
        )
        self.cache.set(key, response)
        return response
