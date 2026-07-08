from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ChatCreateDTO(BaseModel):
    topic_name: str
    topic_description: Optional[str] = None
    knowledge_level: str
    concept_node_id: Optional[UUID] = None


class ChatMessageCreateDTO(BaseModel):
    chat_session_id: UUID
    content: str
    reply_to_message_id: Optional[UUID] = None


class PersonalizationReasonDTO(BaseModel):
    """One entry in the 'Why this response' pill under an assistant message."""
    label: str
    detail: str


class ChatSessionResponseDTO(BaseModel):
    id: UUID
    user_id: UUID
    topic_name: str
    topic_description: Optional[str]
    initial_knowledge_level: str
    current_level: str
    title: Optional[str]
    concept_node_id: Optional[UUID] = None


class ChatSessionListDTO(BaseModel):
    id: UUID
    topic_name: str
    title: Optional[str]
    current_level: str
    created_at: datetime
    concept_node_id: Optional[UUID] = None


class ChatMessageResponseDTO(BaseModel):
    id: UUID
    role: str
    message_type: str
    content: str
    created_at: datetime
    personalization_reasons: Optional[List[PersonalizationReasonDTO]] = None


class ConversationItemDTO(BaseModel):
    id: UUID
    role: str
    message_type: str
    content: str
    created_at: datetime
    # Shape varies with whether the quiz has been attempted, so it stays loose.
    quiz_data: Optional[Dict[str, Any]] = None
    personalization_reasons: Optional[List[PersonalizationReasonDTO]] = None


class DeletedResponseDTO(BaseModel):
    deleted: bool
