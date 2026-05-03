from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class Quiz(BaseEntity):
    __tablename__ = "quizzes"

    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options_json = Column(JSONB, nullable=False)
    correct_option = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    points = Column(Integer, nullable=False)
    hint = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    # Relationships
    session = relationship("ChatSession")
    attempts = relationship("QuizAttempt", back_populates="quiz")
