from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class ConceptNodeDTO(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    difficulty_tier: int
    estimated_minutes: Optional[int] = None
    tags: list[str] = []
    mastery_level: float = 0.0
    confidence: float = 0.0
    next_review_at: Optional[str] = None


class ConceptEdgeDTO(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    relation_type: str
    weight: float


class GraphResponseDTO(BaseModel):
    nodes: list[ConceptNodeDTO]
    edges: list[ConceptEdgeDTO]


class RecommendedConceptDTO(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    difficulty_tier: int
    current_mastery: float


class RecommendationResponseDTO(BaseModel):
    """
    Either a recommendation or an explanation of why there isn't one.

    The endpoint answers `{"message": "..."}` when every unlocked concept is
    already mastered, and the dashboard card branches on that. Both shapes are
    modelled here rather than forcing one, so the existing contract holds.
    """
    id: Optional[UUID] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    difficulty_tier: Optional[int] = None
    current_mastery: Optional[float] = None
    message: Optional[str] = None
