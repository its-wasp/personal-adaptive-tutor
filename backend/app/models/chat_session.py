import enum
from sqlalchemy import Column, String, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class KnowledgeLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class ChatSession(BaseEntity):
    __tablename__ = "chat_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    topic_name = Column(String, nullable=False)
    topic_description = Column(String, nullable=True)
    initial_knowledge_level = Column(Enum(KnowledgeLevel, native_enum=False), nullable=False)
    current_level = Column(Enum(KnowledgeLevel, native_enum=False), nullable=False)
    title = Column(String, nullable=True)
    concept_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=True)
    conversation_summary = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")
    concept_node = relationship("ConceptNode", back_populates="sessions")
