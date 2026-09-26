import httpx
from services.evidence import Evidence
from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

class GNewsClient:
    name = "gnews"
    def __init__(self) -> None: 
        self.api_key = get_settings().gnews_api_key
        self.timeout = get_settings().request_timeout_seconds
        
    @property
    def enabled(self) -> bool: return bool(self.api_key)
    
    async def search(self, query: str, limit: int, client: httpx.AsyncClient | None = None) -> list[Evidence]:
        own_client = client is None
        client = client or httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.get("https://gnews.io/api/v4/search", params={"q": query, "max": limit, "lang": "en", "apikey": self.api_key})
            response.raise_for_status()
            return [Evidence(title=x.get("title", "Untitled"), url=x.get("url", ""), snippet=x.get("description") or "", source=self.name, published_at=x.get("publishedAt")) for x in response.json().get("articles", [])]
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
