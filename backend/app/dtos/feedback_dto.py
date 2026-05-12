from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class MessageFeedbackCreateDTO(BaseModel):
    message_id: UUID
    is_helpful: bool
    feedback_text: Optional[str] = None
    feedback_category: Optional[str] = None  # TOO_COMPLEX, TOO_SIMPLE, JUST_RIGHT, NOT_RELEVANT


class MessageFeedbackResponseDTO(BaseModel):
    id: UUID
    message_id: UUID
    is_helpful: bool
    feedback_text: Optional[str] = None
    feedback_category: Optional[str] = None
