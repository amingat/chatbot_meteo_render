from typing import Literal

from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.prompts import ROUTER_SYSTEM_PROMPT


class RouteDecision(BaseModel):
    route: Literal['rag', 'tool', 'chat']
    reason: str


class QueryRouter:
    def __init__(self, settings: Settings):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        self.router = self.llm.with_structured_output(RouteDecision)

    def route(self, query: str, history: list[dict] | None = None) -> RouteDecision:
        history_text = ''
        if history:
            history_text = '\n'.join(f"{item['role']}: {item['content']}" for item in history[-6:])

        messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    'Historique récent:\n'
                    f'{history_text or "(aucun)"}\n\n'
                    'Question utilisateur:\n'
                    f'{query}'
                )
            ),
        ]
        return self.router.invoke(messages)
