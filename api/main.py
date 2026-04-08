from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ChatRequest,
    ChatResponse,
    ClearMemoryRequest,
    ClearMemoryResponse,
    SessionListResponse,
    SessionMessagesResponse,
)
from app.services.assistant import ClimateAssistantService


app = FastAPI(
    title='Climate RAG Agent API',
    version='1.1.0',
    description='API pour un assistant RAG + Agent spécialisé météo / climat.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

assistant_service = ClimateAssistantService()


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}


@app.get('/sessions', response_model=SessionListResponse)
def list_sessions() -> SessionListResponse:
    return assistant_service.list_sessions()


@app.get('/sessions/{session_id}/messages', response_model=SessionMessagesResponse)
def get_session_messages(session_id: str) -> SessionMessagesResponse:
    return assistant_service.get_session_messages(session_id)


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return assistant_service.chat(session_id=payload.session_id, message=payload.message)


@app.post('/memory/clear', response_model=ClearMemoryResponse)
def clear_memory(payload: ClearMemoryRequest) -> ClearMemoryResponse:
    assistant_service.clear_memory(payload.session_id)
    return ClearMemoryResponse(session_id=payload.session_id, status='cleared')
