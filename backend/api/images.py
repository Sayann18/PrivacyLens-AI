from fastapi import APIRouter, File, HTTPException, UploadFile
from processors.extraction import IMAGE_EXTENSIONS, extract_bytes_async, file_extension
from utils.config import get_settings
from utils.errors import extraction_error_response, structured_http_exception

router = APIRouter()


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    content = bytearray()
    while chunk := await file.read(64 * 1024):
        content.extend(chunk)
        if len(content) > limit:
            raise structured_http_exception(413, "FILE_TOO_LARGE", "The file is too large.")
    return bytes(content)


@router.post("/extract/image")
async def extract_image(file: UploadFile = File(...)) -> dict:
    content_type = (file.content_type or "").lower()
    extension_ok = file_extension(file.filename) in IMAGE_EXTENSIONS
    content_type_ok = content_type.startswith("image/")
    if not extension_ok and not content_type_ok:
        raise structured_http_exception(415, "UNSUPPORTED_FILE_TYPE", "The image endpoint accepts image files only.")
    data = await _read_limited(file, min(get_settings().max_upload_size_bytes, 10 * 1024 * 1024))
    if not data:
        raise structured_http_exception(400, "EMPTY_FILE", "The uploaded file is empty.")
    result = await extract_bytes_async(file.filename, data)
    if result.file_type != "image":
        raise structured_http_exception(415, "UNSUPPORTED_FILE_TYPE", "The image endpoint accepts image files only.")
    if not result.success:
        raise extraction_error_response(422, result)
    if getattr(result, "analyzable", True) is False or result.status == "NO_ANALYZABLE_CONTENT":
        return {
            "success": True,
            "analyzable": False,
            "status": "NO_ANALYZABLE_CONTENT",
            "source": result.filename,
            "text": "",
            "character_count": 0,
            "file_type": result.file_type,
            "metadata": result.metadata,
            "extraction_method": result.extraction_method,
            "confidence": 0.0,
            "warnings": result.warnings,
            "message": result.error or "Nothing to analyze was found in this image. It appears to be a normal image without readable privacy or document text.",
        }
    return {
        "success": True, "source": result.filename, "text": result.text, "character_count": len(result.text),
        "file_type": result.file_type, "metadata": result.metadata, "extraction_method": result.extraction_method,
        "confidence": result.confidence, "warnings": result.warnings,
    }
