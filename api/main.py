from fastapi import FastAPI, HTTPException
import traceback

from app.models import ChatRequest, ClearMemoryRequest
from app.services.assistant import ClimateAssistantService


app = FastAPI(
    title="Climate RAG Agent API",
    version="1.0.0",
    description="API FastAPI pour le chatbot météo/climat avec RAG, outils et mémoire.",
)

assistant = ClimateAssistantService()


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
        return assistant.list_sessions()
    except Exception as exc:
        print("ERREUR /sessions:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    try:
        return assistant.get_session_messages(session_id)
    except Exception as exc:
        print(f"ERREUR /sessions/{session_id}/messages:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/memory/clear")
def clear_memory(payload: ClearMemoryRequest):
    try:
        assistant.clear_memory(payload.session_id)
        return {
            "session_id": payload.session_id,
            "status": "ok",
        }
    except Exception as exc:
        print("ERREUR /memory/clear:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(payload: ChatRequest):
    return {
        "session_id": payload.session_id,
        "route": "chat",
        "answer": "test ok",
        "sources": [],
        "used_tools": [],
    }