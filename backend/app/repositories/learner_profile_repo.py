from sqlalchemy.orm import Session
from app.models.learner_profile import LearnerProfile


class LearnerProfileRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id) -> LearnerProfile | None:
        return (
            self.db.query(LearnerProfile)
            .filter(LearnerProfile.user_id == user_id)
            .first()
        )

    def create(self, profile: LearnerProfile) -> LearnerProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def save(self, profile: LearnerProfile) -> LearnerProfile:
        self.db.commit()
        self.db.refresh(profile)
        return profile
