"""Question bank loading and selection service."""

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Seed data directory
SEED_DATA_DIR = Path(__file__).parent.parent.parent / "seed_data" / "question_banks"

# Module metadata
MODULE_METADATA = {
    "M1": {"name": "Core Identity & Context", "order": 1, "type": "mandatory"},
    "M2": {"name": "Decision Logic & Risk", "order": 2, "type": "mandatory"},
    "M3": {"name": "Preferences & Values", "order": 3, "type": "mandatory"},
    "M4": {"name": "Communication & Social", "order": 4, "type": "mandatory"},
    "A1": {"name": "Lifestyle & Routines", "order": 5, "type": "addon"},
    "A2": {"name": "Spending & Financial Behavior", "order": 6, "type": "addon"},
    "A3": {"name": "Career & Growth Aspirations", "order": 7, "type": "addon"},
    "A4": {"name": "Work & Learning Style", "order": 8, "type": "addon"},
}

# Mapping from module_id to filename
MODULE_FILES = {
    "M1": "M1_core_identity.json",
    "M2": "M2_decision_logic.json",
    "M3": "M3_preferences_values.json",
    "M4": "M4_communication_social.json",
    "A1": "A1_lifestyle_routines.json",
    "A2": "A2_spending_financial.json",
    "A3": "A3_career_growth.json",
    "A4": "A4_work_learning.json",
}


class CompletionCriteria(BaseModel):
    """Module completion criteria."""

    coverage_threshold: float = Field(ge=0.0, le=1.0)
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    min_questions: int = Field(ge=1)
    min_behavioral_rules: int = Field(default=0, ge=0)


class Question(BaseModel):
    """Question from question bank."""

    question_id: str
    question_text: str
    question_type: Literal["open_text", "forced_choice", "scenario", "trade_off", "likert"]
    target_signals: list[str]
    follow_up_triggers: list[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=3)
    estimated_seconds: int = Field(default=30)
    is_followup: bool = False
    parent_question_id: str | None = None
    intent: Literal["EXPLORE", "DEEPEN", "CONTRAST", "CLARIFY", "RESOLVE"] = Field(
        default="EXPLORE", description="Default question intent"
    )


class ModuleQuestionBank(BaseModel):
    """Full question bank for a module."""

    module_id: str
    module_name: str
    module_goal: str
    estimated_duration_min: int
    completion_criteria: CompletionCriteria
    signal_targets: list[str]
    questions: list[Question]


class ModuleInfo(BaseModel):
    """Basic module information."""

    module_id: str
    module_name: str
    module_type: Literal["mandatory", "addon"]
    order: int
    estimated_duration_min: int = 3


class QuestionBankService:
    """Load and manage question banks from JSON files."""

    def __init__(self, seed_data_dir: Path | None = None):
        """Initialize question bank service.

        Args:
            seed_data_dir: Directory containing question bank JSON files.
        """
        self.seed_data_dir = seed_data_dir or SEED_DATA_DIR
        self._cache: dict[str, ModuleQuestionBank] = {}

    def load_question_bank(self, module_id: str) -> ModuleQuestionBank:
        """Load question bank for a module from JSON file.

        Args:
            module_id: Module ID (e.g., "M1", "M2").

        Returns:
            ModuleQuestionBank with all questions and metadata.

        Raises:
            FileNotFoundError: If question bank file doesn't exist.
            ValueError: If module_id is not recognized.
        """
        if module_id in self._cache:
            return self._cache[module_id]

        if module_id not in MODULE_FILES:
            raise ValueError(f"Unknown module ID: {module_id}")

        filename = MODULE_FILES[module_id]
        file_path = self.seed_data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Question bank file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse questions
        questions = [Question(**q) for q in data.get("questions", [])]

        # Build question bank
        question_bank = ModuleQuestionBank(
            module_id=data["module_id"],
            module_name=data["module_name"],
            module_goal=data["module_goal"],
            estimated_duration_min=data.get("estimated_duration_min", 3),
            completion_criteria=CompletionCriteria(**data["completion_criteria"]),
            signal_targets=data["signal_targets"],
            questions=questions,
        )

        self._cache[module_id] = question_bank
        logger.debug(f"Loaded question bank: {module_id} ({len(questions)} questions)")
        return question_bank

    def get_all_modules(self) -> list[ModuleInfo]:
        """Get metadata for all available modules.

        Returns:
            List of ModuleInfo sorted by order.
        """
        modules = []
        for module_id, meta in MODULE_METADATA.items():
            # Only include modules that have question banks
            if module_id in MODULE_FILES:
                modules.append(
                    ModuleInfo(
                        module_id=module_id,
                        module_name=meta["name"],
                        module_type=meta["type"],
                        order=meta["order"],
                        estimated_duration_min=3 if meta["type"] == "mandatory" else 4,
                    )
                )
        return sorted(modules, key=lambda m: m.order)

    def get_mandatory_modules(self) -> list[str]:
        """Get list of mandatory module IDs in order.

        Returns:
            List of module IDs (M1, M2, M3, M4).
        """
        return [m.module_id for m in self.get_all_modules() if m.module_type == "mandatory"]

    def get_question_by_id(self, module_id: str, question_id: str) -> Question | None:
        """Get a specific question by ID.

        Args:
            module_id: Module ID containing the question.
            question_id: Question ID to find.

        Returns:
            Question if found, None otherwise.
        """
        try:
            bank = self.load_question_bank(module_id)
            for q in bank.questions:
                if q.question_id == question_id:
                    return q
            return None
        except (FileNotFoundError, ValueError):
            return None

    def get_next_static_question(
        self,
        module_id: str,
        asked_question_ids: list[str],
    ) -> Question | None:
        """Get next question in priority order (static selection).

        This is the Sprint 1a static selection - questions are returned
        in priority order, skipping already-asked questions.

        Args:
            module_id: Module to get question from.
            asked_question_ids: IDs of questions already asked.

        Returns:
            Next Question or None if no more questions.
        """
        bank = self.load_question_bank(module_id)

        # Sort by priority, then by question_id for consistency
        sorted_questions = sorted(bank.questions, key=lambda q: (q.priority, q.question_id))

        for question in sorted_questions:
            if question.question_id not in asked_question_ids:
                return question

        return None

    def get_questions_for_signal(
        self,
        module_id: str,
        target_signal: str,
        asked_question_ids: list[str] | None = None,
    ) -> list[Question]:
        """Get questions targeting a specific signal.

        Args:
            module_id: Module to search in.
            target_signal: Signal to find questions for.
            asked_question_ids: Optional list of questions to exclude.

        Returns:
            List of questions targeting this signal.
        """
        bank = self.load_question_bank(module_id)
        asked = set(asked_question_ids or [])

        return [
            q
            for q in bank.questions
            if target_signal in q.target_signals and q.question_id not in asked
        ]

    def get_module_completion_criteria(self, module_id: str) -> CompletionCriteria:
        """Get completion thresholds for a module.

        Args:
            module_id: Module ID.

        Returns:
            CompletionCriteria with thresholds.
        """
        bank = self.load_question_bank(module_id)
        return bank.completion_criteria

    def get_signal_targets(self, module_id: str) -> list[str]:
        """Get all target signals for a module.

        Args:
            module_id: Module ID.

        Returns:
            List of signal names.
        """
        bank = self.load_question_bank(module_id)
        return bank.signal_targets

    def get_module_goal(self, module_id: str) -> str:
        """Get the goal description for a module.

        Args:
            module_id: Module ID.

        Returns:
            Module goal string.
        """
        bank = self.load_question_bank(module_id)
        return bank.module_goal

    def get_module_name(self, module_id: str) -> str:
        """Get the human-readable name for a module.

        Args:
            module_id: Module ID.

        Returns:
            Module name string.
        """
        if module_id in MODULE_METADATA:
            return MODULE_METADATA[module_id]["name"]
        bank = self.load_question_bank(module_id)
        return bank.module_name

    def get_first_question(self, module_id: str) -> Question:
        """Get the first question for a module.

        Args:
            module_id: Module ID.

        Returns:
            First question (highest priority).

        Raises:
            ValueError: If module has no questions.
        """
        question = self.get_next_static_question(module_id, [])
        if question is None:
            raise ValueError(f"Module {module_id} has no questions")
        return question

    def clear_cache(self) -> None:
        """Clear the question bank cache."""
        self._cache.clear()


# Singleton instance
_question_bank_service: QuestionBankService | None = None


def get_question_bank_service() -> QuestionBankService:
    """Get the singleton question bank service instance."""
    global _question_bank_service
    if _question_bank_service is None:
        _question_bank_service = QuestionBankService()
    return _question_bank_service
