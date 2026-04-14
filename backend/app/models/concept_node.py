from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base_entity import BaseEntity


class ConceptNode(BaseEntity):
    __tablename__ = "concept_nodes"

    subject = Column(String, nullable=False)  # e.g. "dsa"
    name = Column(String, nullable=False)  # e.g. "binary_search_tree" (unique per subject)
    display_name = Column(String, nullable=False)  # e.g. "Binary Search Tree"
    description = Column(Text, nullable=True)
    difficulty_tier = Column(Integer, nullable=False, default=1)  # 1 (easiest) to 5 (hardest)
    estimated_minutes = Column(Integer, nullable=True)
    tags_json = Column(JSONB, nullable=True)  # e.g. ["trees", "searching", "sorting"]

    # Relationships
    sessions = relationship("ChatSession", back_populates="concept_node")
    masteries = relationship("ConceptMastery", back_populates="concept_node")

    # Edges where this node is the source
    outgoing_edges = relationship(
        "ConceptEdge",
        foreign_keys="ConceptEdge.from_node_id",
        back_populates="from_node",
    )
    # Edges where this node is the target
    incoming_edges = relationship(
        "ConceptEdge",
        foreign_keys="ConceptEdge.to_node_id",
        back_populates="to_node",
    )
