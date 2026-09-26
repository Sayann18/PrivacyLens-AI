from fastapi import APIRouter, HTTPException, Request, UploadFile
from processors.extraction import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, extract_bytes_async, file_extension
from services.document_analyzer import DocumentAnalyzer
from utils.config import get_settings
from utils.errors import extraction_error_response, structured_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
analyzer = DocumentAnalyzer()


async def read_limited(file: UploadFile, limit: int) -> bytes:
    content = bytearray()
    while chunk := await file.read(64 * 1024):
        content.extend(chunk)
        if len(content) > limit:
            raise structured_http_exception(413, "FILE_TOO_LARGE", "The file is too large.")
    return bytes(content)


@router.post("/analyze")
async def analyze_document(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    source, text = "pasted text", None
    extraction_warnings: list[str] = []

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception as exc:
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The request body is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The JSON body must be an object.")
        text = str(payload.get("text", "")).strip()
    else:
        try:
            form = await request.form()
        except Exception as exc:
            raise structured_http_exception(400, "MALFORMED_REQUEST", "The request could not be parsed.") from exc
        uploaded = form.get("file")
        text = str(form.get("text", "")).strip()
        if hasattr(uploaded, "filename") and uploaded.filename:
            limit = get_settings().max_upload_size_bytes
            data = await read_limited(uploaded, limit)
            extracted = await extract_bytes_async(uploaded.filename, data)
            if not extracted.success:
                raise extraction_error_response(422, extracted)
            if getattr(extracted, "analyzable", True) is False or extracted.status == "NO_ANALYZABLE_CONTENT":
                return {
                    "success": True,
                    "analyzable": False,
                    "status": "NO_ANALYZABLE_CONTENT",
                    "source": extracted.filename,
                    "message": extracted.error or "Nothing to analyze was found in this image. It appears to be a normal image without readable privacy or document text.",
                    "warnings": extracted.warnings,
                }
            source, text = extracted.filename, extracted.text
            extraction_warnings = extracted.warnings

    if not text:
        raise structured_http_exception(400, "MISSING_CONTENT", "Provide a supported file or text to analyze.")

    try:
        result = await analyzer.analyze_async(source, text)
    except Exception as exc:
        logger.error("Analysis failed for %s: %s", source, exc, exc_info=True)
        raise structured_http_exception(500, "ANALYSIS_FAILED", "The document could not be analyzed.") from exc

    body = result.model_dump()
    body["success"] = True
    if extraction_warnings:
        body["warnings"] = extraction_warnings
    return body
