from sqlalchemy import Column, Boolean, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class MessageFeedback(BaseEntity):
    __tablename__ = "message_feedback"

    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    is_helpful = Column(Boolean, nullable=False)
    feedback_text = Column(Text, nullable=True)
    feedback_category = Column(String, nullable=True)  # TOO_COMPLEX, TOO_SIMPLE, JUST_RIGHT, NOT_RELEVANT

    # Relationships
    message = relationship("ChatMessage", back_populates="feedback")
