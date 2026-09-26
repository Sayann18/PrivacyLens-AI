from fastapi import APIRouter, File, HTTPException, UploadFile
from processors.extraction import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, extract_bytes_async, file_extension
from api.images import _read_limited
from utils.config import get_settings
from utils.errors import extraction_error_response, structured_http_exception

router = APIRouter()


def _response(result) -> dict:
    return {
        "success": result.success,
        "analyzable": getattr(result, "analyzable", True),
        "status": getattr(result, "status", "SUCCESS"),
        "source": result.filename,
        "text": result.text,
        "character_count": len(result.text),
        "file_type": result.file_type,
        "metadata": result.metadata,
        "extraction_method": result.extraction_method,
        "confidence": result.confidence,
        "truncated": result.truncated,
        "partial": result.partial,
        "warnings": result.warnings,
        "message": result.error if getattr(result, "analyzable", True) is False else None,
    }


@router.post("/extract/file")
async def extract_single_file(file: UploadFile = File(...)) -> dict:
    limit = get_settings().max_upload_size_bytes
    data = await _read_limited(file, limit)
    result = await extract_bytes_async(file.filename, data)
    if not result.success:
        raise extraction_error_response(422, result)
    return _response(result)


@router.post("/extract/files")
async def extract_files(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise structured_http_exception(400, "MISSING_CONTENT", "Please choose at least one file.")
    results = []
    limit = get_settings().max_upload_size_bytes
    total_submitted = len(files)
    total_processed = min(total_submitted, 10)
    for file in files[:10]:
        try:
            data = await _read_limited(file, limit)
            result = await extract_bytes_async(file.filename, data)
            results.append({
                "filename": result.filename,
                "success": result.success,
                "analyzable": getattr(result, "analyzable", True),
                "status": getattr(result, "status", "SUCCESS"),
                "text": result.text,
                "file_type": result.file_type,
                "metadata": result.metadata,
                "error": result.error,
                "error_code": result.error_code,
                "warnings": result.warnings,
                "partial": result.partial,
                "extraction_method": result.extraction_method,
                "confidence": result.confidence,
            })
        except HTTPException as exc:
            detail = exc.detail
            msg = detail.get("error", {}).get("message") if isinstance(detail, dict) else str(detail)
            code = detail.get("error", {}).get("code", "FILE_TOO_LARGE") if isinstance(detail, dict) else "FILE_TOO_LARGE"
            results.append({"filename": file.filename or "upload", "success": False, "error": msg, "error_code": code})
    successful = sum(1 for item in results if item["success"])
    warnings = []
    if total_submitted > 10:
        warnings.append(f"Only the first 10 of {total_submitted} submitted files were processed.")
    return {
        "files": results,
        "total": len(results),
        "total_submitted": total_submitted,
        "total_processed": total_processed,
        "successful": successful,
        "failed": len(results) - successful,
        "warnings": warnings,
    }
