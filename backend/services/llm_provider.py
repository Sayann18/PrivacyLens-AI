from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.groq_provider import GroqProvider
from services.openai_provider import structured_json
from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def extract_facts(self, text: str, schema: str) -> dict[str, Any] | None:
        raise NotImplementedError

    async def summarize(self, text: str) -> str | None:
        return None


class OpenAIProvider(LLMProvider):
    async def extract_facts(self, text: str, schema: str) -> dict[str, Any] | None:
        system = (
            "Extract only facts explicitly or clearly stated in the supplied document. "
            "Do not rate risk, legality, fairness, safety, or quality. Do not infer missing clauses. "
            "For each fact, include a short exact evidence quote copied from the input."
        )
        return await structured_json(system, text, schema)

    async def summarize(self, text: str) -> str | None:
        settings = get_settings()
        if not settings.openai_ready:
            return None
        system = (
            "Write a concise professional 3 to 5 sentence summary of the supplied content. "
            "Use only information present in the input and preserve important user-facing terms. "
            "Do not provide legal advice, risk labels, or implementation details. Return plain text only."
        )
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                max_tokens=700,
                temperature=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text[: settings.openai_max_input_chars]},
                ],
            )
            return (response.choices[0].message.content or "").strip() or None
        except Exception as exc:
            logger.warning("OpenAI summary failed: %s", exc.__class__.__name__)
            return None


class ProviderRouter(LLMProvider):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.groq = GroqProvider()
        self.openai = OpenAIProvider()

    @property
    def ready(self) -> bool:
        return bool(self.settings.llm_enabled and (self.groq.ready or self.settings.openai_ready))

    def _providers(self) -> list[LLMProvider]:
        providers: list[LLMProvider] = []
        primary = self.settings.llm_primary_provider.lower()
        fallback = self.settings.llm_fallback_provider.lower()
        mapping = {"groq": self.groq, "openai": self.openai}
        for name in (primary, fallback):
            provider = mapping.get(name)
            if provider is None or provider in providers:
                continue
            if isinstance(provider, GroqProvider) and not provider.ready:
                continue
            if provider is self.openai and not self.settings.openai_ready:
                continue
            providers.append(provider)
        return providers

    async def extract_facts(self, text: str, schema: str) -> dict[str, Any] | None:
        if not self.settings.llm_enabled:
            return None
        for provider in self._providers():
            try:
                result = await provider.extract_facts(text, schema)
                if result:
                    return result
            except Exception as exc:
                logger.warning("LLM fact extraction failed for %s: %s", provider.__class__.__name__, exc.__class__.__name__)
        return None

    async def summarize(self, text: str) -> str | None:
        if not self.settings.llm_enabled:
            return None
        for provider in self._providers():
            try:
                result = await provider.summarize(text)
                if result:
                    return result
            except Exception as exc:
                logger.warning("LLM summary failed for %s: %s", provider.__class__.__name__, exc.__class__.__name__)
        return None


def get_llm_provider() -> ProviderRouter:
    return ProviderRouter()
