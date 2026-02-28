"""Answer parsing service using LLM."""

import logging
import re
from typing import TYPE_CHECKING

from app.llm import LLMClient, get_llm_client
from app.schemas.llm_responses import ExtractedSignal, ParsedAnswer, ParsedAnswerResponse
from app.services.prompt_service import PromptService, get_prompt_service

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AnswerParserService:
    """Parse and analyze user answers using LLM."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
    ):
        """Initialize answer parser service.

        Args:
            llm_client: LLM client for generating responses.
            prompt_service: Service for loading prompt templates.
        """
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()

    async def parse_answer(
        self,
        module_id: str,
        module_name: str,
        question_text: str,
        target_signal: str,
        answer_text: str,
        previous_answers: list[dict] | None = None,
        signal_targets: list[str] | None = None,
    ) -> ParsedAnswer:
        """Parse answer to extract signals and determine follow-up needs.

        Uses the answer_parser.txt prompt template and LLM to analyze
        the user's answer.

        Args:
            module_id: Current module ID (e.g., "M1").
            module_name: Human-readable module name.
            question_text: The question that was asked.
            target_signal: The signal this question targets.
            answer_text: The user's answer.
            previous_answers: Previous Q&A in this module for context.
            signal_targets: Valid signal names for this module.

        Returns:
            ParsedAnswer with extracted signals and metadata.
        """
        previous_answers = previous_answers or []

        # Format prompt
        prompt = self.prompt_service.get_answer_parser_prompt(
            module_id=module_id,
            module_name=module_name,
            question_text=question_text,
            target_signal=target_signal,
            answer_text=answer_text,
            previous_answers=previous_answers,
            signal_targets=signal_targets,
        )

        # Call LLM with schema validation
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                response_format=ParsedAnswerResponse,
                temperature=0.3,  # Lower temperature for analysis
                metadata={"prompt_name": "answer_parser", "module_id": module_id},
            )
            parsed = ParsedAnswer.from_llm_response(response)
            logger.info(
                f"LLM parsed answer for {module_id}/{target_signal}: "
                f"signals={[s.signal for s in parsed.signals_extracted]}, "
                f"specificity={parsed.specificity_score:.2f}"
            )
            return parsed
        except Exception as e:
            logger.warning(f"LLM answer parsing failed, using heuristics: {e}")
            # Fallback to heuristic parsing
            return self._parse_heuristic(answer_text, target_signal)

    def _parse_heuristic(self, answer_text: str, target_signal: str) -> ParsedAnswer:
        """Fallback heuristic parsing when LLM fails.

        Extracts the target signal when the answer has enough substance,
        so coverage can progress even without the LLM.

        Args:
            answer_text: The user's answer.
            target_signal: The signal this question targets.

        Returns:
            ParsedAnswer with heuristic-based values.
        """
        specificity = self.calculate_heuristic_specificity(answer_text)
        language = self.detect_language_heuristic(answer_text)
        needs_followup = specificity < 0.4

        # Extract target signal if answer has enough substance
        signals: list[ExtractedSignal] = []
        if target_signal and specificity >= 0.2:
            signals.append(
                ExtractedSignal(
                    signal=target_signal,
                    value=answer_text[:200],
                    confidence=min(specificity, 0.7),
                )
            )
        logger.info(
            f"Heuristic parse for {target_signal}: "
            f"specificity={specificity:.2f}, "
            f"signals={[s.signal for s in signals]}"
        )

        return ParsedAnswer(
            specificity_score=specificity,
            signals_extracted=signals,
            behavioral_rules=[],
            needs_followup=needs_followup,
            followup_reason="vague" if needs_followup else None,
            sentiment="neutral",
            language=language,
        )

    def calculate_heuristic_specificity(self, answer_text: str) -> float:
        """Calculate heuristic specificity score for an answer.

        Simple heuristic based on:
        - Length of answer
        - Presence of specific details (numbers, names, etc.)
        - Variety of words

        Args:
            answer_text: The user's answer.

        Returns:
            Specificity score between 0 and 1.
        """
        if not answer_text or not answer_text.strip():
            return 0.0

        text = answer_text.strip()
        word_count = len(text.split())

        # Base score from length (0-0.5)
        length_score = min(word_count / 50, 0.5)

        # Bonus for specific details (0-0.3)
        detail_score = 0.0

        # Check for numbers
        if re.search(r"\d+", text):
            detail_score += 0.1

        # Check for proper nouns (capitalized words not at start)
        proper_nouns = re.findall(r"(?<!^)(?<!\. )[A-Z][a-z]+", text)
        if proper_nouns:
            detail_score += 0.1

        # Check for specific temporal references
        temporal_patterns = r"\b(morning|evening|night|daily|weekly|years?|months?|days?)\b"
        if re.search(temporal_patterns, text, re.IGNORECASE):
            detail_score += 0.1

        # Penalty for very short answers (0-0.2)
        brevity_penalty = 0.0
        if word_count < 5:
            brevity_penalty = 0.2
        elif word_count < 10:
            brevity_penalty = 0.1

        total = length_score + detail_score - brevity_penalty
        return max(0.0, min(1.0, total))

    def detect_language_heuristic(self, text: str) -> str:
        """Detect language of text using simple heuristics.

        Args:
            text: Text to analyze.

        Returns:
            "EN", "HI", or "HG" (Hinglish).
        """
        if not text:
            return "EN"

        # Hindi characters (Devanagari)
        hindi_chars = len(re.findall(r"[\u0900-\u097F]", text))
        total_chars = len(re.sub(r"\s", "", text))

        if total_chars == 0:
            return "EN"

        hindi_ratio = hindi_chars / total_chars

        if hindi_ratio > 0.5:
            return "HI"
        elif hindi_ratio > 0.1:
            return "HG"  # Hinglish (mixed)
        else:
            return "EN"


# Singleton instance
_answer_parser_service: AnswerParserService | None = None


def get_answer_parser_service() -> AnswerParserService:
    """Get the singleton answer parser service instance."""
    global _answer_parser_service
    if _answer_parser_service is None:
        _answer_parser_service = AnswerParserService()
    return _answer_parser_service
