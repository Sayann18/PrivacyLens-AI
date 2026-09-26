import asyncio
import httpx
from services.evidence import Evidence
from search.gnews import GNewsClient
from search.google_factcheck import GoogleFactCheckClient
from search.newsapi import NewsApiClient
from search.tavily import TavilyClient
from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    def __init__(self) -> None:
        self.providers = [TavilyClient(), NewsApiClient(), GNewsClient(), GoogleFactCheckClient()]

    async def search(self, claim: str, limit: int) -> tuple[list[Evidence], list[str]]:
        enabled = [provider for provider in self.providers if provider.enabled]
        if not enabled:
            return [], []
            
        settings = get_settings()
        timeout = settings.request_timeout_seconds + 5
        
        evidence: list[Evidence] = []
        checked: list[str] = []
        
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            tasks = [provider.search(claim, limit, client) for provider in enabled]
            
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error("Global search timeout reached")
                return evidence, checked

            for provider, result in zip(enabled, results):
                if isinstance(result, Exception):
                    logger.error(f"Provider {provider.name} raised unexpected error: {result}")
                    continue
                checked.append(provider.name)
                evidence.extend(result)
                
        return evidence, checked
