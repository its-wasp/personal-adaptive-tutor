from sqlalchemy.orm import Session
from app.models.topic_progress import TopicProgress


class AnalyticsRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_user_progress(self, user_id) -> list[TopicProgress]:
        return (
            self.db.query(TopicProgress)
            .filter(TopicProgress.user_id == user_id)
            .all()
        )
