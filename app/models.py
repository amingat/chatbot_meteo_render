from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    excerpt: str | None = None
    relevance: float | None = None


class ChatMessageItem(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    created_at: str
    route: Literal['rag', 'tool', 'chat'] | None = None
    used_tools: list[str] = []
    sources: list[SourceItem] = []


class SessionSummary(BaseModel):
    session_id: str
    message_count: int
    started_at: str
    updated_at: str
    first_message_preview: str | None = None
    last_message_preview: str | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    route: Literal['rag', 'tool', 'chat']
    answer: str
    sources: list[SourceItem] = []
    used_tools: list[str] = []


class ClearMemoryRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


class ClearMemoryResponse(BaseModel):
    session_id: str
    status: str


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageItem]
