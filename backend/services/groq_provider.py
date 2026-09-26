from __future__ import annotations

import json
from typing import Any

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class GroqProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = bool(self.settings.groq_enabled and self.settings.groq_api_key)
        self._client = None

    @property
    def ready(self) -> bool:
        return self.enabled

    def _get_client(self):
        if not self.enabled:
            return None
        if self._client is None:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(
                    api_key=self.settings.groq_api_key,
                    timeout=self.settings.groq_timeout_seconds,
                )
            except Exception as exc:
                logger.warning("Groq client unavailable: %s", exc.__class__.__name__)
                return None
        return self._client

    async def _request(self, messages: list[dict[str, Any]], json_mode: bool = False) -> str | None:
        client = self._get_client()
        if client is None:
            return None
        for attempt in range(max(1, self.settings.groq_max_retries + 1)):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.settings.groq_model,
                    "messages": messages,
                    "temperature": 0,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                if json_mode:
                    kwargs["max_tokens"] = 4000
                else:
                    kwargs["max_tokens"] = 700
                response = await client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                return content.strip() or None
            except Exception as exc:
                logger.warning("Groq request attempt %s failed: %s", attempt + 1, exc.__class__.__name__)
        return None

    async def extract_facts(self, text: str, schema: str) -> dict[str, Any] | None:
        payload = text[: self.settings.groq_max_input_chars]
        system = (
            "Extract only facts explicitly supported by the supplied content. "
            "Do not judge legality, safety, fairness, or risk. "
            "Do not infer missing clauses. Every fact must include an exact evidence quote copied from the input. "
            f"Return only JSON matching this shape: {schema}"
        )
        raw = await self._request(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": payload},
            ],
            json_mode=True,
        )
        if raw is None:
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    async def summarize(self, text: str) -> str | None:
        payload = text[: self.settings.groq_max_input_chars]
        system = (
            "Write a concise professional summary of the supplied content in 3 to 5 sentences. "
            "State what the document or webpage is about, the main purpose, and the most relevant user-facing points. "
            "Use only information present in the input. Preserve important names, prices, dates, permissions, obligations, and conditions when relevant. "
            "Do not invent facts. Do not give legal advice. Do not label the content safe, unsafe, illegal, a scam, or risk-free. "
            "Do not mention the AI model, PrivacyLens AI internals, prompts, rules, or extraction methods."
        )
        return await self._request(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": payload},
            ]
        )
