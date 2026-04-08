import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class SQLiteMemoryStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    meta_json TEXT
                )
                """
            )
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(chat_messages)').fetchall()}
            if 'meta_json' not in columns:
                conn.execute('ALTER TABLE chat_messages ADD COLUMN meta_json TEXT')
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO chat_messages (session_id, role, content, created_at, meta_json) VALUES (?, ?, ?, ?, ?)',
                (
                    session_id,
                    role,
                    content,
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None,
                ),
            )
            conn.commit()

    def get_messages(self, session_id: str, limit: int | None = 12) -> list[dict[str, Any]]:
        query = (
            """
            SELECT role, content, created_at, meta_json
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            """
        )
        params: tuple[Any, ...]
        if limit is not None:
            query += ' LIMIT ?'
            params = (session_id, limit)
        else:
            params = (session_id,)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        rows = list(reversed(rows))
        messages: list[dict[str, Any]] = []
        for row in rows:
            payload: dict[str, Any] = {
                'role': row['role'],
                'content': row['content'],
                'created_at': row['created_at'],
            }
            meta_json = row['meta_json']
            if meta_json:
                try:
                    payload.update(json.loads(meta_json))
                except json.JSONDecodeError:
                    pass
            messages.append(payload)
        return messages

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            session_rows = conn.execute(
                """
                SELECT session_id,
                       COUNT(*) AS message_count,
                       MIN(created_at) AS started_at,
                       MAX(created_at) AS updated_at,
                       MAX(id) AS last_id
                FROM chat_messages
                GROUP BY session_id
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            sessions: list[dict[str, Any]] = []
            for row in session_rows:
                first_row = conn.execute(
                    """
                    SELECT content
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY id ASC
                    LIMIT 1
                    """,
                    (row['session_id'],),
                ).fetchone()
                last_row = conn.execute(
                    """
                    SELECT content
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (row['session_id'],),
                ).fetchone()
                sessions.append(
                    {
                        'session_id': row['session_id'],
                        'message_count': row['message_count'],
                        'started_at': row['started_at'],
                        'updated_at': row['updated_at'],
                        'first_message_preview': self._preview(first_row['content'] if first_row else None),
                        'last_message_preview': self._preview(last_row['content'] if last_row else None),
                    }
                )
        return sessions

    @staticmethod
    def _preview(text: str | None, max_len: int = 80) -> str | None:
        if not text:
            return None
        text = ' '.join(text.split())
        return text[:max_len] + ('…' if len(text) > max_len else '')

    def clear(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
            conn.commit()
