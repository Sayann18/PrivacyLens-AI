from __future__ import annotations

from fastapi import HTTPException


def error_body(code: str, message: str, details: dict | None = None, warnings: list[str] | None = None) -> dict:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "warnings": warnings or [],
    }


def structured_http_exception(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_body(code, message, details))


def extraction_error_response(status_code: int, result) -> HTTPException:
    code = result.error_code or "UNREADABLE_DOCUMENT"
    if code == "UNSUPPORTED_FILE_TYPE":
        status = 415
    elif code in {"EMPTY_FILE", "EMPTY_DOCUMENT", "MISSING_CONTENT", "MALFORMED_REQUEST"}:
        status = 400
    elif code in {"FILE_TOO_LARGE", "DOCUMENT_TOO_LARGE"}:
        status = 413
    elif code == "SERVICE_UNAVAILABLE":
        status = 503
    elif code in {"CORRUPTED_DOCUMENT", "CORRUPTED_IMAGE", "UNSUPPORTED_ENCODING", "ENCRYPTED_DOCUMENT", "UNREADABLE_DOCUMENT", "OCR_UNAVAILABLE"}:
        status = 422
    else:
        status = status_code or 422
    return structured_http_exception(status, code, result.error or "This file could not be processed.")
