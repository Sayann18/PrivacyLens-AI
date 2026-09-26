from pydantic import BaseModel, Field, HttpUrl


class VerifyRequest(BaseModel):
    claim: str = Field(min_length=8, max_length=2_000, description="Claim to verify")
    max_results: int = Field(default=10, ge=1, le=30)
    force_refresh: bool = False


class UrlRequest(BaseModel):
    url: HttpUrl
    max_chars: int = Field(default=12_000, ge=500, le=100_000)
