from sqlalchemy.orm import Session
from app.repositories.engagement_repo import EngagementRepository
from app.models.engagement_event import EngagementEvent, EventType


class EngagementService:

    def __init__(self, db: Session):
        self.repo = EngagementRepository(db)

    def track_event(
        self,
        user_id,
        event_type: EventType,
        chat_session_id=None,
        concept_node_id=None,
        payload: dict = None,
    ):
        event = EngagementEvent(
            user_id=user_id,
            event_type=event_type,
            chat_session_id=chat_session_id,
            concept_node_id=concept_node_id,
            payload_json=payload,
        )
        return self.repo.create_event(event)
