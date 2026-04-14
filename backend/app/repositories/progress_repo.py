from sqlalchemy.orm import Session
from app.models.topic_progress import TopicProgress


class ProgressRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_progress(self, user_id, topic_name) -> TopicProgress | None:
        return (
            self.db.query(TopicProgress)
            .filter(TopicProgress.user_id == user_id, TopicProgress.topic_name == topic_name)
            .first()
        )

    def create_progress(self, progress: TopicProgress) -> TopicProgress:
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def save(self, progress: TopicProgress) -> TopicProgress:
        self.db.commit()
        self.db.refresh(progress)
        return progress
