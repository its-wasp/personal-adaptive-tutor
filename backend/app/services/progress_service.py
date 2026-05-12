from sqlalchemy.orm import Session
from app.repositories.progress_repo import ProgressRepository
from app.models.topic_progress import TopicProgress


LEVEL_THRESHOLDS = {
    "BEGINNER": 0,
    "INTERMEDIATE": 50,
    "ADVANCED": 150,
}


class ProgressService:

    def __init__(self, db: Session):
        self.repo = ProgressRepository(db)

    def update_progress(self, user_id, topic_name, points_awarded, is_correct):
        progress = self.repo.get_progress(user_id, topic_name)

        if not progress:
            progress = TopicProgress(
                user_id=user_id,
                topic_name=topic_name,
                total_points=0,
                current_level="BEGINNER",
                quizzes_attempted=0,
                quizzes_correct=0,
            )
            progress = self.repo.create_progress(progress)

        progress.quizzes_attempted += 1
        if is_correct:
            progress.quizzes_correct += 1
            progress.total_points += points_awarded

        progress.current_level = self._determine_level(progress.total_points)
        return self.repo.save(progress)

    def _determine_level(self, total_points: int) -> str:
        level = "BEGINNER"
        for name, threshold in LEVEL_THRESHOLDS.items():
            if total_points >= threshold:
                level = name
        return level
