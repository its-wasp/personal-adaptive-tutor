from sqlalchemy.orm import Session
from app.models.chat_session import ChatSession
from app.search.factory import get_search_provider


class ReferenceService:

    def __init__(self, db: Session):
        self.db = db
        self.search = get_search_provider()

    def get_references(self, chat_session_id):
        session = self.db.query(ChatSession).filter(
            ChatSession.id == chat_session_id
        ).first()

        if not session:
            raise ValueError("Chat session not found")

        topic = session.topic_name
        articles = self.search.search(f"{topic} tutorial", categories="general", num_results=3)
        videos = self.search.search(f"{topic} tutorial", categories="videos", num_results=2)

        return {
            "topic_name": topic,
            "articles": articles,
            "videos": videos,
        }
