import time
import uuid
from collections import defaultdict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            
            
            raise
        response.headers["X-Request-ID"] = request_id
        return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


async def global_exception_handler(request: Request, exc: Exception):
    request_id = _request_id(request)
    logger.error("Unhandled exception on %s [request_id=%s]: %s", request.url.path, request_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred. Please try again.", "details": None},
            "warnings": [],
            "request_id": request_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = _request_id(request)
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = {**detail, "request_id": request_id}
        body.setdefault("success", False)
        body.setdefault("warnings", [])
    else:
        body = {
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": str(detail), "details": None},
            "warnings": [],
            "request_id": request_id,
        }
    headers = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content=body, headers=headers)


async def validation_exception_handler(request: Request, exc: Exception):
    request_id = _request_id(request)
    code = "MALFORMED_REQUEST"
    message = "Please check your input and try again."

    errors = getattr(exc, "errors", None)
    if callable(errors):
        err_list = errors()
        if err_list:
            first = err_list[0]
            loc = [str(l) for l in first.get("loc", []) if l not in {"body", "query", "path"}]
            msg = first.get("msg", "")
            err_type = first.get("type", "")
            if "url" in loc or "url" in err_type:
                code = "INVALID_URL"
                message = "Please enter a valid public HTTP or HTTPS web address."
            elif loc:
                message = f"Invalid input for {'.'.join(loc)}: {msg}"
            else:
                message = msg or "Invalid request parameters."

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {"code": code, "message": message, "details": None},
            "warnings": [],
            "request_id": request_id,
        },
    )


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.settings = get_settings()

    def _cleanup(self, now):
        cutoff = now - 60
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]

    async def __call__(self, request: Request):
        now = time.time()
        if int(now) % 10 == 0:
            self._cleanup(now)

        ip = request.client.host if request.client else "127.0.0.1"

        cutoff = now - 60
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]

        if len(self.requests[ip]) >= self.settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"success": False, "error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "details": None}, "warnings": []},
                headers={"Retry-After": "60"},
            )

        self.requests[ip].append(now)


rate_limiter = RateLimiter()
