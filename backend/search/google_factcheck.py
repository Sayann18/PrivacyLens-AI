import httpx
from services.evidence import Evidence
from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

class GoogleFactCheckClient:
    name = "google_factcheck"
    def __init__(self) -> None: 
        self.api_key = get_settings().google_factcheck_api_key
        self.timeout = get_settings().request_timeout_seconds
        
    @property
    def enabled(self) -> bool: return bool(self.api_key)
    
    async def search(self, query: str, limit: int, client: httpx.AsyncClient | None = None) -> list[Evidence]:
        own_client = client is None
        client = client or httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.get("https://factchecktools.googleapis.com/v1alpha1/claims:search", params={"query": query, "pageSize": limit, "key": self.api_key})
            response.raise_for_status()
            
            items: list[Evidence] = []
            for claim in response.json().get("claims", []):
                for review in claim.get("claimReview", []):
                    items.append(Evidence(title=claim.get("text", "Fact check"), url=review.get("url", ""), snippet=f"{review.get('textualRating', '')}: {review.get('title', '')}", source=self.name, published_at=review.get("reviewDate")))
            return items
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limited by {self.name}")
            else:
                logger.error(f"{self.name} search failed: HTTP {e.response.status_code}")
            return []
        except httpx.TimeoutException:
            logger.error(f"{self.name} search timed out")
            return []
        except httpx.RequestError as e:
            logger.error(f"{self.name} search request error: {e}")
            return []
        except Exception as e:
            logger.error(f"{self.name} search unexpected error: {e}")
            return []
        finally:
            if own_client:
                await client.aclose()
