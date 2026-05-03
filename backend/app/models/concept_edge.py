import enum
from sqlalchemy import Column, Enum, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class RelationType(str, enum.Enum):
    PREREQUISITE = "PREREQUISITE"  # from_node must be learned before to_node
    RELATED = "RELATED"  # concepts are related but no strict ordering
    EXTENDS = "EXTENDS"  # to_node builds directly on from_node


class ConceptEdge(BaseEntity):
    __tablename__ = "concept_edges"

    from_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=False)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("concept_nodes.id"), nullable=False)
    relation_type = Column(Enum(RelationType, native_enum=False), nullable=False)
    weight = Column(Float, default=1.0)  # 0.0 to 1.0, strength of dependency

    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", "relation_type", name="uq_concept_edge"),
    )

    # Relationships
    from_node = relationship("ConceptNode", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node = relationship("ConceptNode", foreign_keys=[to_node_id], back_populates="incoming_edges")
