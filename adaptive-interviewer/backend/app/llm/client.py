"""Thin LiteLLM wrapper — same pattern as the ai-interviewer service.

Exposes:
    - LLMClient.generate(prompt, system, response_format?) -> dict|model
    - generate(...) module-level convenience
    - A separate client instance tuned for classifier calls (lower
      temperature, JSON mode) via get_classifier_client()
"""

import asyncio
import json
import logging
from typing import Any, TypeVar

import litellm
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

litellm.set_verbose = settings.debug

if settings.langfuse_public_key and settings.langfuse_secret_key:
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]


T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        model: str | None = None,
        max_retries: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = 60.0,
    ):
        self.model = model or settings.llm_model
        self.max_retries = max_retries or settings.llm_max_retries
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: type[T] | None = None,
        history: list[dict[str, str]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | T | str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                coro = litellm.acompletion(
                    model=self.model,
                    messages=messages,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    response_format=({"type": "json_object"} if response_format else None),
                    metadata=metadata or {},
                )
                response = await asyncio.wait_for(coro, timeout=self.timeout) if self.timeout else await coro
                content = response.choices[0].message.content
                if not content:
                    raise LLMError("Empty response from LLM")
                if response_format:
                    try:
                        return response_format.model_validate(json.loads(content))
                    except (json.JSONDecodeError, ValidationError) as e:
                        raise LLMError(f"Invalid JSON response: {e}")
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt * 0.5, 8.0))
                    continue
                raise LLMError(f"LLM failed after {self.max_retries} attempts: {e}")
        raise LLMError(f"LLM failed: {last_error}")


_default: LLMClient | None = None
_classifier: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _default
    if _default is None:
        _default = LLMClient()
    return _default


def get_classifier_client() -> LLMClient:
    global _classifier
    if _classifier is None:
        _classifier = LLMClient(
            model=settings.llm_classifier_model,
            temperature=0.1,
            max_tokens=600,
        )
    return _classifier


async def generate(prompt: str, **kwargs: Any) -> dict[str, Any] | str:
    return await get_llm_client().generate(prompt=prompt, **kwargs)
