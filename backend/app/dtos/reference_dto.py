from uuid import UUID
from pydantic import BaseModel


class ReferenceRequestDTO(BaseModel):
    chat_session_id: UUID


class ReferenceItemDTO(BaseModel):
    title: str
    url: str
    snippet: str


class ReferenceResponseDTO(BaseModel):
    topic_name: str
    articles: list[ReferenceItemDTO]
    videos: list[ReferenceItemDTO]
