"""AI provider abstraction.

The stylist depends on the :class:`AIProvider` protocol rather than a concrete
vendor. Two implementations ship:

* :class:`OpenAIProvider` — calls the OpenAI Chat/Vision APIs when a key is set.
* :class:`NullProvider` — a no-op used when no key is configured, so the app is
  fully functional offline (the rule-based stylist handles everything).

Selecting a provider is centralized in :func:`get_ai_provider`, making it easy
to add other vendors later without touching call sites.
"""

from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

from app.core.config import settings


@runtime_checkable
class AIProvider(Protocol):
    """Behavior the stylist expects from an AI backend."""

    @property
    def enabled(self) -> bool:
        """Whether this provider can actually make AI calls."""
        ...

    async def complete_json(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any] | None:
        """Return a structured JSON completion, or ``None`` on failure."""
        ...

    async def describe_image(self, image_bytes: bytes, prompt: str) -> dict[str, Any] | None:
        """Return structured attributes for an image, or ``None``."""
        ...


class NullProvider:
    """Offline provider — every call is a no-op returning ``None``."""

    @property
    def enabled(self) -> bool:
        return False

    async def complete_json(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any] | None:
        return None

    async def describe_image(
        self, image_bytes: bytes, prompt: str
    ) -> dict[str, Any] | None:
        return None


class OpenAIProvider:
    """OpenAI-backed provider using the official SDK's async client."""

    def __init__(self) -> None:
        # Imported lazily so the package is only required when a key is set.
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._vision_model = settings.openai_vision_model

    @property
    def enabled(self) -> bool:
        return True

    async def complete_json(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any] | None:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = resp.choices[0].message.content
            return json.loads(content) if content else None
        except Exception:
            # Any API/parse error falls back to the rule-based stylist.
            return None

    async def describe_image(
        self, image_bytes: bytes, prompt: str
    ) -> dict[str, Any] | None:
        import base64

        try:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            resp = await self._client.chat.completions.create(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}"
                                },
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = resp.choices[0].message.content
            return json.loads(content) if content else None
        except Exception:
            return None


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider (OpenAI if keyed, else offline)."""
    if settings.ai_enabled:
        return OpenAIProvider()
    return NullProvider()
