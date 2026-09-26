from __future__ import annotations

import re

from services.llm_provider import LLMProvider, get_llm_provider


class SummaryService:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    @staticmethod
    def _fallback(text: str) -> str:
        cleaned = re.sub(r"```.*?```", " ", text, flags=re.S)
        cleaned = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", cleaned)
        cleaned = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", cleaned)
        cleaned = re.sub(r"[`*_#>-]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", cleaned) if item.strip()]
        chosen = [sentence for sentence in sentences if len(sentence.split()) >= 6][:4]
        if not chosen:
            return "No readable content was available for a concise summary."
        return " ".join(chosen)[:1200]

    def _payload(self, text: str) -> str:
        from utils.config import get_settings
        limit = get_settings().groq_max_input_chars if get_settings().groq_ready else get_settings().openai_max_input_chars
        if len(text) <= limit:
            return text
        part = limit // 3
        return text[:part] + "\n[...middle content omitted for summary context...]\n" + text[len(text) // 2 - part // 2 : len(text) // 2 + part // 2] + "\n[...middle-end content omitted...]\n" + text[-part:]

    async def summarize(self, text: str) -> tuple[str, bool]:
        cleaned = text.strip()
        if not cleaned:
            return "No readable content was available for a concise summary.", False
        payload = self._payload(cleaned)
        result = await self.provider.summarize(payload)
        if result:
            normalized = re.sub(r"\s+", " ", result).strip()
            return normalized[:1600], True
        return self._fallback(cleaned), False
