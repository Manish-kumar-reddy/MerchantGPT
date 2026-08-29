from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    session_id: UUID | None = None
    message: str


class SendMessageResponse(BaseModel):
    session_id: UUID
    reply: str
    tool_calls_made: list[str] = []
