from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class LearnerProfile(BaseEntity):
    __tablename__ = "learner_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # Learning preferences (set during onboarding or inferred)
    learning_style = Column(String, nullable=True)  # VISUAL, READING, EXAMPLE_FIRST, THEORY_FIRST
    pace_preference = Column(String, nullable=True)  # QUICK, MODERATE, DETAILED
    explanation_detail_level = Column(String, default="STANDARD")  # CONCISE, STANDARD, VERBOSE
    preferred_code_complexity = Column(String, default="SIMPLE")  # SIMPLE, MODERATE, ADVANCED
    analogy_preference = Column(Boolean, default=True)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)

    # Engagement stats (computed from events)
    total_sessions = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=0)
    avg_session_duration_minutes = Column(Float, nullable=True)
    preferred_session_time = Column(String, nullable=True)  # morning, afternoon, evening, night

    # Streaks
    streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)

    # Strengths and weaknesses (computed from mastery data)
    strengths_json = Column(JSONB, nullable=True)  # list of concept tags the user excels at
    weaknesses_json = Column(JSONB, nullable=True)  # list of concept tags where mastery is low

    # Learner memory — natural language summary that accumulates across sessions
    learner_summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="learner_profile")
