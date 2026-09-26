from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile
import httpx
from fastapi.responses import JSONResponse

from processors.extraction import extract_bytes_async
from processors.normalizer import DocumentNormalizer
from processors.url_processor import extract_url
from services.analysis_pipeline import AnalysisPipeline
from utils.config import get_settings
from utils.errors import extraction_error_response, structured_http_exception
from utils.logger import get_logger

router = APIRouter()
pipeline = AnalysisPipeline()
logger = get_logger(__name__)


async def _read_limited(upload: UploadFile, limit: int) -> bytes:
    data = bytearray()
    while chunk := await upload.read(64 * 1024):
        data.extend(chunk)
        if len(data) > limit:
            raise structured_http_exception(413, "FILE_TOO_LARGE", "The file is too large.")
    return bytes(data)


@router.post("/analyses")
async def create_analysis(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    normalizer = DocumentNormalizer()
    document = None
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception as exc:
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The request body is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The JSON body must be an object.")
        text = str(payload.get("text", "")).strip()
        url = str(payload.get("url", "")).strip()
        if text:
            document = normalizer.from_text(text)
        elif url:
            try:
                document = normalizer.from_url_result(await extract_url(url, int(payload.get("max_chars", 100_000))))
            except httpx.TimeoutException as exc:
                raise structured_http_exception(504, "TIMEOUT", "The webpage took too long to retrieve.") from exc
            except httpx.HTTPStatusError as exc:
                raise structured_http_exception(422, "URL_UNREACHABLE", "We couldn't access that webpage. Check that the URL is public and available, then try again.") from exc
            except httpx.RequestError as exc:
                raise structured_http_exception(422, "URL_UNREACHABLE", "We couldn't access that webpage. Check that the URL is public and available, then try again.") from exc
            except ValueError as exc:
                raise structured_http_exception(422, "URL_UNREADABLE", str(exc)) from exc
        else:
            raise structured_http_exception(400, "MISSING_CONTENT", "Provide text, a supported file, or a public URL to analyze.")
    else:
        try:
            form = await request.form()
        except Exception as exc:
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The request could not be parsed.") from exc
        text = str(form.get("text", "")).strip()
        url = str(form.get("url", "")).strip()
        upload = form.get("file")
        if upload is not None and hasattr(upload, "filename") and upload.filename:
            data = await _read_limited(upload, get_settings().max_upload_size_bytes)
            result = await extract_bytes_async(upload.filename, data)
            if not result.success:
                raise extraction_error_response(422, result)
            if not result.analyzable or result.status == "NO_ANALYZABLE_CONTENT":
                raise structured_http_exception(422, "NO_ANALYZABLE_CONTENT", result.error or "No readable text was found in the supplied file.")
            document = normalizer.from_extraction_result(result)
            if result.truncated:
                document = document.model_copy(update={"partial": True, "warnings": [*document.warnings, "Extracted text was truncated to the configured safety limit."]})
        elif text:
            document = normalizer.from_text(text)
        elif url:
            try:
                document = normalizer.from_url_result(await extract_url(url, 100_000))
            except httpx.TimeoutException as exc:
                raise structured_http_exception(504, "TIMEOUT", "The webpage took too long to retrieve.") from exc
            except httpx.HTTPStatusError as exc:
                raise structured_http_exception(422, "URL_UNREACHABLE", "We couldn't access that webpage. Check that the URL is public and available, then try again.") from exc
            except httpx.RequestError as exc:
                raise structured_http_exception(422, "URL_UNREACHABLE", "We couldn't access that webpage. Check that the URL is public and available, then try again.") from exc
            except ValueError as exc:
                raise structured_http_exception(422, "URL_UNREADABLE", str(exc)) from exc
        else:
            raise structured_http_exception(400, "MISSING_CONTENT", "Provide text, a supported file, or a public URL to analyze.")

    if document is None or not document.raw_text.strip():
        raise structured_http_exception(422, "NO_READABLE_CONTENT", "No readable text was found in the supplied content.")
    try:
        report = await pipeline.analyze(document)
        return report.model_dump(mode="json")
    except Exception as exc:
        logger.error("Analysis pipeline failed: %s", exc, exc_info=True)
        raise structured_http_exception(500, "ANALYSIS_FAILED", "The document could not be analyzed.") from exc


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str) -> dict:
    report = pipeline.get(analysis_id)
    if report is None:
        raise structured_http_exception(404, "ANALYSIS_NOT_FOUND", "That analysis is no longer available.")
    return report.model_dump(mode="json")
