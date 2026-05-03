import enum
from sqlalchemy import Column, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class EventType(str, enum.Enum):
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"
    MESSAGE_SENT = "MESSAGE_SENT"
    QUIZ_STARTED = "QUIZ_STARTED"
    QUIZ_COMPLETED = "QUIZ_COMPLETED"
    EXPLANATION_VIEWED = "EXPLANATION_VIEWED"
    HINT_REQUESTED = "HINT_REQUESTED"
    FEEDBACK_GIVEN = "FEEDBACK_GIVEN"
    RESOURCE_CLICKED = "RESOURCE_CLICKED"


class EngagementEvent(BaseEntity):
    __tablename__ = "engagement_events"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(EventType, native_enum=False), nullable=False)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    concept_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=True)
    payload_json = Column(JSONB, nullable=True)  # event-specific data

    # Relationships
    user = relationship("User", back_populates="engagement_events")
