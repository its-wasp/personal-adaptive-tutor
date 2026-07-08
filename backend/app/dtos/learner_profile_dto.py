from typing import Optional
from pydantic import BaseModel


class LearnerPreferencesDTO(BaseModel):
    learning_style: Optional[str] = None  # VISUAL, READING, EXAMPLE_FIRST, THEORY_FIRST
    pace_preference: Optional[str] = None  # QUICK, MODERATE, DETAILED
    explanation_detail_level: Optional[str] = None  # CONCISE, STANDARD, VERBOSE
    preferred_code_complexity: Optional[str] = None  # SIMPLE, MODERATE, ADVANCED
    analogy_preference: Optional[bool] = None


class PreferencesUpdatedDTO(BaseModel):
    message: str
    learning_style: Optional[str] = None


class LearnerProfileResponseDTO(BaseModel):
    """
    What GET /profile/me returns.

    Note the field is `use_analogies`, not `analogy_preference` — the latter is
    the column name, but get_personalization_context renames it on the way out
    and the Profile page reads the renamed form. The DTO previously declared
    the column name, so wiring it up as a response_model would have silently
    dropped the toggle from the payload.
    """
    learning_style: Optional[str] = None
    pace_preference: Optional[str] = None
    explanation_detail_level: Optional[str] = None
    preferred_code_complexity: Optional[str] = None
    use_analogies: bool = True
    onboarding_completed: bool = False
    total_sessions: int = 0
    streak_days: int = 0
    strengths: list[str] = []
    weaknesses: list[str] = []
    learner_summary: Optional[str] = None
