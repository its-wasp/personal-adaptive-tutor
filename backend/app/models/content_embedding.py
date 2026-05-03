from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector
from app.models.base_entity import BaseEntity


class ContentEmbedding(BaseEntity):
    __tablename__ = "content_embeddings"

    content_type = Column(String, nullable=False)  # EXPLANATION, QUIZ_EXPLANATION, REFERENCE_SNIPPET
    source_id = Column(UUID(as_uuid=True), nullable=True)  # FK to originating record (polymorphic)
    concept_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=True)
    content_text = Column(Text, nullable=False)  # the original text that was embedded
    content_summary = Column(String, nullable=True)  # short label for display
    difficulty_level = Column(String, nullable=True)
    metadata_json = Column(JSONB, nullable=True)  # tags, source info
    embedding = Column(Vector(384), nullable=True)  # all-MiniLM-L6-v2 produces 384-dim vectors
