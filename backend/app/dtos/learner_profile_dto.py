from typing import Optional
from pydantic import BaseModel


class LearnerPreferencesDTO(BaseModel):
    learning_style: Optional[str] = None  # VISUAL, READING, EXAMPLE_FIRST, THEORY_FIRST
    pace_preference: Optional[str] = None  # QUICK, MODERATE, DETAILED
    explanation_detail_level: Optional[str] = None  # CONCISE, STANDARD, VERBOSE
    preferred_code_complexity: Optional[str] = None  # SIMPLE, MODERATE, ADVANCED
    analogy_preference: Optional[bool] = None


class LearnerProfileResponseDTO(BaseModel):
    learning_style: Optional[str] = None
    pace_preference: Optional[str] = None
    explanation_detail_level: Optional[str] = None
    preferred_code_complexity: Optional[str] = None
    analogy_preference: bool = True
    onboarding_completed: bool = False
    total_sessions: int = 0
    streak_days: int = 0
    strengths: list[str] = []
    weaknesses: list[str] = []
