import enum
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(BaseEntity):
    __tablename__ = "users"

    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.USER)

    # Relationships
    sessions = relationship("ChatSession", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    topic_progress = relationship("TopicProgress", back_populates="user")
    learner_profile = relationship("LearnerProfile", back_populates="user", uselist=False)
    engagement_events = relationship("EngagementEvent", back_populates="user")
    concept_masteries = relationship("ConceptMastery", back_populates="user")
