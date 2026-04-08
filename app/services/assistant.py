import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.memory.store import SQLiteMemoryStore
from app.models import ChatResponse, SessionListResponse, SessionMessagesResponse
from app.prompts import AGENT_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT
from app.rag.retriever import ClimateRAG
from app.router import QueryRouter
from app.tools.calculator import calculator_tool
from app.tools.todo import todo_tool
from app.tools.weather import weather_tool
from app.tools.web_search import web_search_tool


class ClimateAssistantService:
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise RuntimeError(
                'OPENAI_API_KEY est obligatoire pour le backend FastAPI. '
                'Définissez-la dans Render ou dans votre fichier .env.'
            )
        self.memory = SQLiteMemoryStore(self.settings.sqlite_path)
        self.router = QueryRouter(self.settings)
        self.rag = ClimateRAG(self.settings)
        self.chat_llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=0.2,
            api_key=self.settings.openai_api_key,
        )
        self.tools = [calculator_tool, weather_tool, web_search_tool, todo_tool]
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.agent_llm = self.chat_llm.bind_tools(self.tools)

    def _history_to_messages(self, history: list[dict]):
        messages = []
        for item in history:
            role = item['role']
            content = item['content']
            if role == 'user':
                messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                messages.append(AIMessage(content=content))
        return messages

    def _run_chat(self, query: str, history: list[dict]) -> str:
        messages = [SystemMessage(content=CHAT_SYSTEM_PROMPT)]
        messages.extend(self._history_to_messages(history[-8:]))
        messages.append(HumanMessage(content=query))
        response = self.chat_llm.invoke(messages)
        return response.content

    def _run_agent(self, query: str, history: list[dict]) -> tuple[str, list[str]]:
        messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
        messages.extend(self._history_to_messages(history[-8:]))
        messages.append(HumanMessage(content=query))
        used_tools: list[str] = []

        for _ in range(4):
            response = self.agent_llm.invoke(messages)
            messages.append(response)

            if not getattr(response, 'tool_calls', None):
                return response.content, used_tools

            for call in response.tool_calls:
                tool_name = call['name']
                tool_args = call.get('args', {}) or {}
                tool = self.tool_map[tool_name]
                tool_result = tool.invoke(tool_args)
                used_tools.append(tool_name)
                messages.append(
                    ToolMessage(
                        content=tool_result if isinstance(tool_result, str) else json.dumps(tool_result, ensure_ascii=False),
                        tool_call_id=call['id'],
                        name=tool_name,
                    )
                )

        final_response = self.chat_llm.invoke(messages)
        return final_response.content, used_tools

    def chat(self, session_id: str, message: str) -> ChatResponse:
        history = self.memory.get_messages(session_id=session_id, limit=12)
        decision = self.router.route(message, history)

        if decision.route == 'rag':
            answer, sources = self.rag.answer(message, history)
            used_tools = []
            if not sources:
                fallback_answer, used_tools = self._run_agent(
                    f"Les documents internes sont insuffisants. Réponds à la question suivante en utilisant un outil si nécessaire: {message}",
                    history,
                )
                answer = fallback_answer
            route = 'rag'
        elif decision.route == 'tool':
            answer, used_tools = self._run_agent(message, history)
            sources = []
            route = 'tool'
        else:
            answer = self._run_chat(message, history)
            sources = []
            used_tools = []
            route = 'chat'

        self.memory.add_message(session_id, 'user', message)
        self.memory.add_message(
            session_id,
            'assistant',
            answer,
            metadata={
                'route': route,
                'used_tools': used_tools,
                'sources': [source.model_dump() for source in sources],
            },
        )

        return ChatResponse(
            session_id=session_id,
            route=route,
            answer=answer,
            sources=sources,
            used_tools=used_tools,
        )

    def clear_memory(self, session_id: str) -> None:
        self.memory.clear(session_id)

    def list_sessions(self) -> SessionListResponse:
        return SessionListResponse(sessions=self.memory.list_sessions())

    def get_session_messages(self, session_id: str) -> SessionMessagesResponse:
        return SessionMessagesResponse(
            session_id=session_id,
            messages=self.memory.get_messages(session_id=session_id, limit=None),
        )
