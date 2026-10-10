"""Cliente LLM ligero con soporte de Tool Calling (API compatible con OpenAI).

Soporta Ollama (local), OpenAI y DeepSeek. Si no hay proveedor configurado,
el agente usa el modo determinista offline (planner basado en NLP).
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings

DEFAULT_MODELS: dict[str, tuple[str, str]] = {
    "ollama": ("http://localhost:11434/v1", "llama3.1"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "openai_compatible": ("", ""),
}


class LLMError(RuntimeError):
    pass


class LLMBackend:
    def __init__(
        self,
        *,
        provider: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def model_label(self) -> str:
        return self.model or self.provider

    def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> dict:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": tools,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM no disponible ({self.provider}): {exc}") from exc

        choice = response.json()["choices"][0]["message"]
        tool_calls: list[dict] = []
        for call in choice.get("tool_calls") or []:
            function = call.get("function") or {}
            raw_args = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_args)
            except (ValueError, TypeError):
                arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append(
                {"id": call.get("id") or "", "name": function.get("name") or "", "arguments": arguments}
            )
        return {"content": choice.get("content") or "", "tool_calls": tool_calls}


def get_llm_backend() -> LLMBackend | None:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()
    if not provider:
        return None
    defaults = DEFAULT_MODELS.get(provider, ("", ""))
    base_url = settings.llm_base_url.strip() or defaults[0]
    model = settings.llm_model.strip() or defaults[1]
    if not base_url or not model:
        return None
    return LLMBackend(
        provider=provider,
        base_url=base_url,
        api_key=settings.llm_api_key.strip(),
        model=model,
        timeout=settings.llm_timeout,
    )


def llm_configured() -> bool:
    return get_llm_backend() is not None