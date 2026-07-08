from uuid import UUID
from typing import Optional, Dict
from pydantic import BaseModel


class QuizGenerateDTO(BaseModel):
    chat_session_id: UUID


class QuizSubmitDTO(BaseModel):
    quiz_id: UUID
    selected_option: str


class QuizResponseDTO(BaseModel):
    """
    A freshly generated quiz.

    Deliberately carries no hint, explanation or correct_option: all three give
    the answer away, and the client only needs them once an attempt exists.
    """
    id: UUID
    question_text: str
    options_json: Dict[str, str]
    difficulty: str
    points: int


class QuizSubmitResponseDTO(BaseModel):
    """The graded result — this is where the answer key is finally revealed."""
    correct: bool
    correct_option: str
    points_awarded: int
    explanation: Optional[str] = None
    hint: Optional[str] = None
    new_level: str
    total_points: int
