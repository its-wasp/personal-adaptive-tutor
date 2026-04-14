from sqlalchemy.orm import Session
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.message_feedback import MessageFeedback
from app.models.engagement_event import EngagementEvent


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session: ChatSession) -> ChatSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id) -> ChatSession | None:
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def create_message(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_message(self, message_id) -> ChatMessage | None:
        return self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()

    def get_user_sessions(self, user_id) -> list[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def get_session_messages(self, chat_session_id) -> list[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.chat_session_id == chat_session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def get_recent_messages(self, chat_session_id, limit: int = 20) -> list[ChatMessage]:
        """Get the most recent messages for a session, returned in chronological order."""
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.chat_session_id == chat_session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def get_message_count(self, chat_session_id) -> int:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.chat_session_id == chat_session_id)
            .count()
        )

    def delete_session(self, chat_session_id) -> None:
        """Delete a chat session and all dependent records in FK-safe order."""
        message_ids = [
            m.id for m in self.db.query(ChatMessage.id)
            .filter(ChatMessage.chat_session_id == chat_session_id).all()
        ]
        quiz_ids = [
            q.id for q in self.db.query(Quiz.id)
            .filter(Quiz.chat_session_id == chat_session_id).all()
        ]

        if quiz_ids:
            self.db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
        if message_ids:
            self.db.query(MessageFeedback).filter(MessageFeedback.message_id.in_(message_ids)).delete(synchronize_session=False)

        self.db.query(ChatMessage).filter(ChatMessage.chat_session_id == chat_session_id).delete(synchronize_session=False)
        if quiz_ids:
            self.db.query(Quiz).filter(Quiz.id.in_(quiz_ids)).delete(synchronize_session=False)

        # Preserve engagement history by nulling the session reference instead of deleting
        self.db.query(EngagementEvent).filter(
            EngagementEvent.chat_session_id == chat_session_id
        ).update({EngagementEvent.chat_session_id: None}, synchronize_session=False)

        self.db.query(ChatSession).filter(ChatSession.id == chat_session_id).delete(synchronize_session=False)
        self.db.commit()
