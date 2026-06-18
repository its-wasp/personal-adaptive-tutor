from sqlalchemy.orm import Session
from app.models.message_feedback import MessageFeedback
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


class FeedbackRepository:

    def __init__(self, db: Session):
        self.db = db

    def message_belongs_to_user(self, message_id, user_id) -> bool:
        """True when `message_id` sits in a chat session owned by `user_id`."""
        return (
            self.db.query(ChatMessage.id)
            .join(ChatSession, ChatSession.id == ChatMessage.chat_session_id)
            .filter(ChatMessage.id == message_id, ChatSession.user_id == user_id)
            .first()
            is not None
        )

    def create_feedback(self, feedback: MessageFeedback) -> MessageFeedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_recent_by_user(self, user_id, limit: int = 10) -> list[MessageFeedback]:
        """Get recent feedback from a user, ordered newest first."""
        return (
            self.db.query(MessageFeedback)
            .join(ChatMessage, ChatMessage.id == MessageFeedback.message_id)
            .join(ChatMessage.session)
            .filter(ChatMessage.session.has(user_id=user_id))
            .order_by(MessageFeedback.created_at.desc())
            .limit(limit)
            .all()
        )
