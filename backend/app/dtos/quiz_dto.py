from uuid import UUID
from typing import Optional, Dict
from pydantic import BaseModel


class QuizGenerateDTO(BaseModel):
    chat_session_id: UUID


class QuizSubmitDTO(BaseModel):
    quiz_id: UUID
    selected_option: str


class QuizResponseDTO(BaseModel):
    id: UUID
    question_text: str
    options_json: Dict[str, str]
    difficulty: str
    points: int
    hint: Optional[str] = None
    explanation: Optional[str] = None
