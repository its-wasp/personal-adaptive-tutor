from typing import Optional
from pydantic import BaseModel


class ReviewItemDTO(BaseModel):
    """One concept due for spaced-repetition review."""
    concept_node_id: str
    concept_name: str
    mastery_level: float
    confidence: float
    days_overdue: float
    review_interval_days: float
    ease_factor: float
    last_reviewed_at: Optional[str] = None


class ReviewStatsDTO(BaseModel):
    due_now: int
    upcoming_reviews: int
    total_concepts_studied: int


class ReviewQueueResponseDTO(BaseModel):
    reviews: list[ReviewItemDTO]
    stats: ReviewStatsDTO
