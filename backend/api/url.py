from fastapi import APIRouter
import httpx
from models.request import UrlRequest
from processors.url_processor import extract_url
from utils.errors import structured_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/extract/url")
async def extract_url_endpoint(payload: UrlRequest) -> dict:
    try:
        result = await extract_url(str(payload.url), payload.max_chars)
        return {
            "success": True, "source": result.source, "final_url": result.final_url,
            "content_type": result.content_kind, "text": result.text,
            "character_count": result.character_count, "warnings": result.warnings,
        }
    except ValueError as exc:
        raise structured_http_exception(422, "URL_UNREADABLE", str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise structured_http_exception(504, "URL_TIMEOUT", "The request to that URL timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise structured_http_exception(502, "URL_UPSTREAM_ERROR", f"The site returned an error (HTTP {exc.response.status_code}).") from exc
    except httpx.RequestError as exc:
        logger.info("Unable to retrieve URL %s: %s", payload.url, exc.__class__.__name__)
        raise structured_http_exception(502, "URL_UNREACHABLE", "Could not retrieve that website. Please check the URL and try again.") from exc
    except Exception as exc:
        logger.error("Error extracting URL: %s", exc, exc_info=True)
        raise structured_http_exception(500, "INTERNAL_ERROR", "An unexpected error occurred.") from exc
