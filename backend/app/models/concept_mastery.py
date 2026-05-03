from sqlalchemy import Column, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class ConceptMastery(BaseEntity):
    __tablename__ = "concept_mastery"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=False)

    mastery_level = Column(Float, default=0.0)  # 0.0 (no knowledge) to 1.0 (mastered)
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0, how sure the system is
    total_interactions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)

    # Spaced repetition (SM-2 algorithm)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    review_interval_days = Column(Float, default=1.0)
    ease_factor = Column(Float, default=2.5)

    __table_args__ = (
        UniqueConstraint("user_id", "concept_node_id", name="uq_user_concept"),
    )

    # Relationships
    user = relationship("User", back_populates="concept_masteries")
    concept_node = relationship("ConceptNode", back_populates="masteries")
