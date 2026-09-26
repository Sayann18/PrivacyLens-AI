import os
from dataclasses import dataclass, field
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    
    tavily_api_key: str | None = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    news_api_key: str | None = field(default_factory=lambda: os.getenv("NEWS_API_KEY"))
    gnews_api_key: str | None = field(default_factory=lambda: os.getenv("GNEWS_API_KEY"))
    google_factcheck_api_key: str | None = field(default_factory=lambda: os.getenv("GOOGLE_FACTCHECK_API_KEY") or os.getenv("GOOGLE_FACT_CHECK_API_KEY"))

    
    llm_enabled: bool = field(default_factory=lambda: _bool_env("LLM_ENABLED", True))
    llm_primary_provider: str = field(default_factory=lambda: os.getenv("LLM_PRIMARY_PROVIDER", "groq"))
    llm_fallback_provider: str = field(default_factory=lambda: os.getenv("LLM_FALLBACK_PROVIDER", "openai"))
    groq_enabled: bool = field(default_factory=lambda: _bool_env("GROQ_ENABLED", False))
    groq_api_key: str | None = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    groq_timeout_seconds: int = field(default_factory=lambda: _int_env("GROQ_TIMEOUT_SECONDS", 60))
    groq_max_retries: int = field(default_factory=lambda: _int_env("GROQ_MAX_RETRIES", 2))
    groq_max_input_chars: int = field(default_factory=lambda: _int_env("GROQ_MAX_INPUT_CHARS", 60_000))

    openai_enabled: bool = field(default_factory=lambda: _bool_env("OPENAI_ENABLED", True))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_vision_model: str = field(default_factory=lambda: os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")))
    openai_embedding_model: str = field(default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    openai_timeout_seconds: int = field(default_factory=lambda: _int_env("OPENAI_TIMEOUT_SECONDS", 60))
    openai_max_retries: int = field(default_factory=lambda: _int_env("OPENAI_MAX_RETRIES", 2))
    openai_max_input_chars: int = field(default_factory=lambda: _int_env("OPENAI_MAX_INPUT_CHARS", 60_000))

    
    cache_ttl_seconds: int = field(default_factory=lambda: _int_env("CACHE_TTL_SECONDS", 3600))
    allowed_origins: str = field(default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:5173"))
    max_upload_size_bytes: int = field(default_factory=lambda: _int_env("MAX_UPLOAD_SIZE_BYTES", 20 * 1024 * 1024))
    request_timeout_seconds: int = field(default_factory=lambda: _int_env("REQUEST_TIMEOUT_SECONDS", 30))
    rate_limit_per_minute: int = field(default_factory=lambda: _int_env("RATE_LIMIT_PER_MINUTE", 30))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    
    tesseract_cmd: str | None = field(default_factory=lambda: os.getenv("TESSERACT_CMD"))
    ocr_timeout_seconds: int = field(default_factory=lambda: _int_env("OCR_TIMEOUT_SECONDS", 25))
    max_pdf_pages: int = field(default_factory=lambda: _int_env("MAX_PDF_PAGES", 100))
    max_extracted_text_chars: int = field(default_factory=lambda: _int_env("MAX_EXTRACTED_TEXT_CHARS", 200_000))
    max_sheet_rows: int = field(default_factory=lambda: _int_env("MAX_SHEET_ROWS", 10_000))
    max_zip_uncompressed_bytes: int = field(default_factory=lambda: _int_env("MAX_ZIP_UNCOMPRESSED_BYTES", 100 * 1024 * 1024))
    max_url_response_bytes: int = field(default_factory=lambda: _int_env("MAX_URL_RESPONSE_BYTES", 25 * 1024 * 1024))

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def openai_ready(self) -> bool:
        return bool(self.openai_enabled and self.openai_api_key)

    @property
    def groq_ready(self) -> bool:
        return bool(self.groq_enabled and self.groq_api_key)

    @property
    def llm_ready(self) -> bool:
        return bool(self.llm_enabled and (self.groq_ready or self.openai_ready))

    @property
    def llm_timeout_seconds(self) -> int:
        if self.llm_primary_provider.lower() == "groq" and self.groq_ready:
            return self.groq_timeout_seconds
        return self.openai_timeout_seconds


@lru_cache
def get_settings() -> Settings:
    return Settings()
