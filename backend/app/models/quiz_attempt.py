from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class QuizAttempt(BaseEntity):
    __tablename__ = "quiz_attempts"

    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    selected_option = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    points_awarded = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
