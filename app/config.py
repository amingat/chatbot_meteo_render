from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-4o-mini', alias='OPENAI_MODEL')
    openai_embedding_model: str = Field(default='text-embedding-3-small', alias='OPENAI_EMBEDDING_MODEL')
    docs_path: str = Field(default='data/pdfs', alias='DOCS_PATH')
    chroma_dir: str = Field(default='storage/chroma', alias='CHROMA_DIR')
    sqlite_path: str = Field(default='storage/memory/chat_history.db', alias='SQLITE_PATH')
    todo_path: str = Field(default='storage/memory/todo.json', alias='TODO_PATH')
    api_base_url: str = Field(default='http://localhost:8000', alias='API_BASE_URL')
    tavily_api_key: str | None = Field(default=None, alias='TAVILY_API_KEY')
    app_runtime_mode: Literal['api', 'direct', 'auto'] = Field(default='api', alias='APP_RUNTIME_MODE')
    top_k: int = Field(default=4, alias='TOP_K')
    rag_score_threshold: float = Field(default=0.2, alias='RAG_SCORE_THRESHOLD')

    @property
    def docs_dir(self) -> Path:
        return Path(self.docs_path)

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_dir)

    @property
    def sqlite_db_path(self) -> Path:
        return Path(self.sqlite_path)

    @property
    def todo_file_path(self) -> Path:
        return Path(self.todo_path)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    settings.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.todo_file_path.parent.mkdir(parents=True, exist_ok=True)
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    return settings
