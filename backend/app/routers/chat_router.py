from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.chat_service import ChatService
from app.dtos.chat_dto import ChatCreateDTO, ChatMessageCreateDTO

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/create")
def create_chat(
    dto: ChatCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    try:
        session = service.create_chat(
            user_id=current_user.id,
            topic_name=dto.topic_name,
            topic_description=dto.topic_description,
            knowledge_level=dto.knowledge_level,
            concept_node_id=dto.concept_node_id,
        )
    except ValueError as e:
        # Parse/validation failure from the LLM layer — 502 (bad gateway)
        # is a better fit than 500 since the backend worked, the upstream
        # model returned unusable output.
        raise HTTPException(status_code=502, detail=str(e))
    return {
        "id": session.id,
        "user_id": session.user_id,
        "topic_name": session.topic_name,
        "topic_description": session.topic_description,
        "initial_knowledge_level": session.initial_knowledge_level.value,
        "current_level": session.current_level.value,
        "title": session.title,
        "concept_node_id": session.concept_node_id,
    }


@router.post("/message")
def send_message(
    dto: ChatMessageCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    message = service.send_message(
        chat_session_id=dto.chat_session_id,
        user_id=current_user.id,
        content=dto.content,
        reply_to_message_id=dto.reply_to_message_id,
    )
    return {
        "id": message.id,
        "role": message.role.value,
        "message_type": message.message_type.value,
        "content": message.content,
        "created_at": message.created_at,
    }


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    sessions = service.list_user_sessions(current_user.id)
    return [
        {
            "id": s.id,
            "topic_name": s.topic_name,
            "title": s.title,
            "current_level": s.current_level.value,
            "created_at": s.created_at,
        }
        for s in sessions
    ]


@router.get("/{chat_session_id}/conversation")
def get_conversation(
    chat_session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    return service.get_conversation(chat_session_id, current_user.id)


@router.delete("/{chat_session_id}")
def delete_session(
    chat_session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    deleted = service.delete_session(chat_session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"deleted": True}
