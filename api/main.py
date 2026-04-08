from fastapi import FastAPI, HTTPException
import traceback

from app.config import get_settings
from app.models import ChatRequest, ClearMemoryRequest
from app.services.assistant import ClimateAssistantService


settings = get_settings()
assistant = ClimateAssistantService(settings)

app = FastAPI(
    title="Climate RAG Agent API",
    version="1.0.0",
    description="API FastAPI pour le chatbot météo/climat avec RAG, outils et mémoire.",
)


@app.get("/")
def root():
    return {
        "message": "API chatbot météo active",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sessions")
def list_sessions():
    try:
        sessions = assistant.get_sessions()
        return {"sessions": sessions}
    except Exception as exc:
        print("ERREUR /sessions:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    try:
        messages = assistant.get_session_messages(session_id)
        return {"messages": messages}
    except Exception as exc:
        print("ERREUR /sessions/{session_id}/messages:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/memory/clear")
def clear_memory(payload: ClearMemoryRequest):
    try:
        assistant.clear_session_memory(payload.session_id)
        return {
            "status": "ok",
            "message": f"Mémoire effacée pour la session {payload.session_id}",
        }
    except Exception as exc:
        print("ERREUR /memory/clear:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(payload: ChatRequest):
    try:
        return assistant.chat(payload.session_id, payload.message)
    except Exception as exc:
        print("ERREUR /chat:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))