from sqlalchemy.orm import Session
from app.repositories.analytics_repo import AnalyticsRepository


class AnalyticsService:

    def __init__(self, db: Session):
        self.repo = AnalyticsRepository(db)

    def get_user_analytics(self, user_id):
        progress_list = self.repo.get_user_progress(user_id)

        total_points = sum(p.total_points for p in progress_list)
        total_attempted = sum(p.quizzes_attempted for p in progress_list)
        total_correct = sum(p.quizzes_correct for p in progress_list)
        overall_accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0.0

        topics = []
        for p in progress_list:
            accuracy = (p.quizzes_correct / p.quizzes_attempted * 100) if p.quizzes_attempted > 0 else 0.0
            topics.append({
                "topic_name": p.topic_name,
                "current_level": p.current_level,
                "total_points": p.total_points,
                "quizzes_attempted": p.quizzes_attempted,
                "quizzes_correct": p.quizzes_correct,
                "accuracy_percentage": round(accuracy, 2),
            })

        return {
            "total_topics": len(progress_list),
            "total_points": total_points,
            "total_quizzes_attempted": total_attempted,
            "total_quizzes_correct": total_correct,
            "overall_accuracy_percentage": round(overall_accuracy, 2),
            "topics": topics,
        }
