from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.analysis import router as analysis_router
from api.analyses import router as analyses_router
from api.files import router as files_router
from api.images import router as images_router
from api.url import router as url_router
from api.verify import router as verify_router
from processors.extraction import local_ocr_available
from fastapi.exceptions import RequestValidationError
from utils.config import get_settings
from utils.middleware import (
    RequestIDMiddleware,
    global_exception_handler,
    http_exception_handler,
    rate_limiter,
    validation_exception_handler,
)

settings = get_settings()
app = FastAPI(title="PrivacyLens AI", version="1.0.0", description="Evidence-based claim verification API")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(verify_router, prefix="/api", tags=["verification"], dependencies=[Depends(rate_limiter)])
app.include_router(url_router, prefix="/api", tags=["content"], dependencies=[Depends(rate_limiter)])
app.include_router(files_router, prefix="/api", tags=["content"], dependencies=[Depends(rate_limiter)])
app.include_router(images_router, prefix="/api", tags=["content"], dependencies=[Depends(rate_limiter)])
app.include_router(analysis_router, prefix="/api", tags=["analysis"], dependencies=[Depends(rate_limiter)])
app.include_router(analyses_router, prefix="/api", tags=["analysis-v2"], dependencies=[Depends(rate_limiter)])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "PrivacyLens AI"}


@app.get("/ready")
async def ready() -> dict:
    current = get_settings()
    try:
        pdf_ok = True
        import pypdf  
    except ImportError:
        pdf_ok = False
    try:
        import fitz  
        pdf_render_ok = True
    except ImportError:
        pdf_render_ok = False

    components = {
        "pdf_extraction": pdf_ok,
        "pdf_page_rendering_for_ocr": pdf_render_ok,
        "local_ocr": local_ocr_available(),
        "openai": current.openai_ready,
        "groq": current.groq_ready,
        "llm": current.llm_ready,
        "search_tavily": bool(current.tavily_api_key),
        "search_newsapi": bool(current.news_api_key),
        "search_gnews": bool(current.gnews_api_key),
        "search_google_factcheck": bool(current.google_factcheck_api_key),
    }
    return {"status": "ready", "components": components}
