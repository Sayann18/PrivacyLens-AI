from __future__ import annotations

import base64
import json

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIUnavailable(Exception):
    pass


def _client():
    settings = get_settings()
    if not settings.openai_ready:
        raise OpenAIUnavailable("OpenAI is not configured")
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise OpenAIUnavailable("openai package is not installed") from exc
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)


def is_configured() -> bool:
    return get_settings().openai_ready


async def vision_ocr(image_bytes: bytes, mime_type: str = "image/png") -> str | None:
    settings = get_settings()
    try:
        client = _client()
    except OpenAIUnavailable:
        return None

    b64 = base64.b64encode(image_bytes).decode("ascii")
    last_error: Exception | None = None
    for attempt in range(max(1, settings.openai_max_retries + 1)):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_vision_model,
                max_tokens=4000,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You transcribe visible text from images exactly as it appears. "
                            "Do not summarize, translate, or invent text. If no readable text "
                            "is present, respond with an empty string."
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe all readable text from this image."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                        ],
                    },
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            return text
        except Exception as exc:  
            last_error = exc
            logger.warning("OpenAI vision OCR attempt %s failed: %s", attempt + 1, exc.__class__.__name__)
    logger.error("OpenAI vision OCR unavailable after retries: %s", last_error.__class__.__name__ if last_error else "unknown")
    return None


async def clean_extracted_text(text: str) -> str | None:
    settings = get_settings()
    if not text.strip():
        return None
    try:
        client = _client()
    except OpenAIUnavailable:
        return None
    payload = text[: settings.openai_max_input_chars]
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=4000,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Clean up noisy OCR/extraction text: fix broken line breaks and stray "
                        "characters, but preserve every fact, clause, number, and the original "
                        "structure/order. Do not summarize, remove content, or add anything that "
                        "is not already present. Return only the cleaned text."
                    ),
                },
                {"role": "user", "content": payload},
            ],
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception as exc:  
        logger.warning("OpenAI text cleanup failed: %s", exc.__class__.__name__)
        return None


async def structured_json(system_prompt: str, user_content: str, schema_hint: str) -> dict | None:
    settings = get_settings()
    try:
        client = _client()
    except OpenAIUnavailable:
        return None
    payload = user_content[: settings.openai_max_input_chars]
    last_error: Exception | None = None
    for attempt in range(max(1, settings.openai_max_retries + 1)):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                max_tokens=4000,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nRespond ONLY with JSON matching: {schema_hint}"},
                    {"role": "user", "content": payload},
                ],
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except (json.JSONDecodeError,) as exc:
            last_error = exc
            logger.warning("OpenAI structured output was not valid JSON (attempt %s)", attempt + 1)
        except Exception as exc:  
            last_error = exc
            logger.warning("OpenAI structured call attempt %s failed: %s", attempt + 1, exc.__class__.__name__)
    logger.error("OpenAI structured output unavailable after retries: %s", last_error.__class__.__name__ if last_error else "unknown")
    return None
