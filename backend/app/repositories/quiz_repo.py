from sqlalchemy.orm import Session
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt


class QuizRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_quiz(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def get_quiz(self, quiz_id) -> Quiz | None:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def create_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def get_attempt_for_user(self, quiz_id, user_id) -> QuizAttempt | None:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.created_at.desc())
            .first()
        )
