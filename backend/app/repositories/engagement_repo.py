from sqlalchemy.orm import Session
from app.models.engagement_event import EngagementEvent, EventType


class EngagementRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: EngagementEvent) -> EngagementEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_user_events(self, user_id, event_type: EventType = None, limit: int = 100):
        query = self.db.query(EngagementEvent).filter(EngagementEvent.user_id == user_id)
        if event_type:
            query = query.filter(EngagementEvent.event_type == event_type)
        return query.order_by(EngagementEvent.created_at.desc()).limit(limit).all()

    def count_user_events(self, user_id, event_type: EventType = None) -> int:
        query = self.db.query(EngagementEvent).filter(EngagementEvent.user_id == user_id)
        if event_type:
            query = query.filter(EngagementEvent.event_type == event_type)
        return query.count()
