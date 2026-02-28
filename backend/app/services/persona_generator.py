"""Persona summary generator — creates compact natural-language persona from structured profile."""

import logging
from typing import Any

from app.llm import LLMClient, get_llm_client
from app.schemas.llm_responses import PersonaSummaryResponse
from app.services.prompt_service import PromptService, get_prompt_service

logger = logging.getLogger(__name__)

# Max character length for persona summary (~2500 tokens ~ 10000 chars)
MAX_PERSONA_CHARS = 10000


class PersonaGeneratorService:
    """Generate compact persona summary from structured profile."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()

    async def generate_summary(
        self,
        structured_profile: dict[str, Any],
        modules_included: list[str],
        uncertainty_flags: list[str] | None = None,
    ) -> PersonaSummaryResponse:
        """Generate a first-person persona summary from a structured profile.

        Args:
            structured_profile: The full structured profile JSON.
            modules_included: List of module IDs included in the profile.
            uncertainty_flags: Domains where data is missing.

        Returns:
            PersonaSummaryResponse with persona_summary_text, key_traits, token_estimate.
        """
        import json

        uncertainty_flags = uncertainty_flags or []

        prompt = self.prompt_service.format_prompt(
            "persona_summary",
            structured_profile=json.dumps(structured_profile, indent=2),
            modules_included=", ".join(modules_included),
            uncertainty_flags=", ".join(uncertainty_flags) if uncertainty_flags else "None",
        )

        logger.info(
            f"Generating persona summary for {len(modules_included)} modules"
        )

        result = await self.llm_client.generate(
            prompt=prompt,
            response_format=PersonaSummaryResponse,
            temperature=0.5,  # Moderate creativity for natural writing
            max_tokens=3000,
            metadata={"task": "persona_summary"},
        )

        # Validate length — truncate if needed
        if len(result.persona_summary_text) > MAX_PERSONA_CHARS:
            logger.warning(
                f"Persona summary too long ({len(result.persona_summary_text)} chars), "
                f"truncating to {MAX_PERSONA_CHARS}"
            )
            result.persona_summary_text = result.persona_summary_text[:MAX_PERSONA_CHARS]

        logger.info(
            f"Persona summary generated: {len(result.persona_summary_text)} chars, "
            f"{len(result.key_traits)} key traits"
        )
        return result


# Singleton
_service: PersonaGeneratorService | None = None


def get_persona_generator_service() -> PersonaGeneratorService:
    """Get the singleton persona generator service."""
    global _service
    if _service is None:
        _service = PersonaGeneratorService()
    return _service
