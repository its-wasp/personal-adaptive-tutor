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


class OnboardingStatusDTO(BaseModel):
    onboarding_completed: bool


class MessageResponseDTO(BaseModel):
    message: str


class PlacementQuestionDTO(BaseModel):
    """A placement question as served to the client — no correct answer."""
    index: int
    question: str
    options: dict[str, str]
    tier: int


class PlacementQuizResponseDTO(BaseModel):
    questions: list[PlacementQuestionDTO]


class PlacementResultDTO(BaseModel):
    question_index: int
    is_correct: bool
    correct_option: str
    tier: int


class PlacementSubmitResponseDTO(BaseModel):
    total_questions: int
    correct_answers: int
    score_percentage: float
    assessed_level: str
    results: list[PlacementResultDTO]
