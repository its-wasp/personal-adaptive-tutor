from typing import Optional
from pydantic import BaseModel


class OnboardingPreferencesDTO(BaseModel):
    learning_style: str  # VISUAL, READING, EXAMPLE_FIRST, THEORY_FIRST
    pace_preference: str  # QUICK, MODERATE, DETAILED
    explanation_detail_level: Optional[str] = "STANDARD"
    preferred_code_complexity: Optional[str] = "SIMPLE"
    use_analogies: Optional[bool] = True


class PlacementAnswerDTO(BaseModel):
    question_index: int
    selected_option: str  # A, B, C, D


class PlacementSubmitDTO(BaseModel):
    answers: list[PlacementAnswerDTO]
