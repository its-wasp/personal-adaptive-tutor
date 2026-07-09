from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.engagement_event import EngagementEvent, EventType


class EngagementRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_active_dates(self, user_id, limit_days: int = 400) -> list:
        """
        Distinct calendar dates on which the user produced any engagement
        event, newest first. Used to derive the study streak.

        Capped at `limit_days` because a streak only ever needs the recent
        run — there's no reason to drag a multi-year history into memory.
        """
        day = func.date(EngagementEvent.created_at)
        rows = (
            self.db.query(day)
            .filter(EngagementEvent.user_id == user_id)
            .distinct()
            .order_by(day.desc())
            .limit(limit_days)
            .all()
        )
        return [r[0] for r in rows]

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
