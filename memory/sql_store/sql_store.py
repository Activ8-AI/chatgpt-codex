"""
SQLite-backed persistence utilities for Codex runtime services.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, Optional

from configs import get_database_path


class SQLStore:
    """
    Thin wrapper around sqlite3 with a minimal schema for ledger events.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or get_database_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def record_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> int:
        """
        Insert a new ledger event.
        """
        serialized = json.dumps(payload or {})
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO ledger (event_type, payload) VALUES (?, ?)",
                (event_type, serialized),
            )
            return int(cursor.lastrowid)

    def fetch_events(
        self, *, event_type: Optional[str] = None, limit: int = 50
    ) -> Iterable[Dict[str, Any]]:
        """
        Return recent events, newest first.
        """
        query = "SELECT id, event_type, payload, created_at FROM ledger"
        params = []
        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._lock, self._connection:
            cursor = self._connection.execute(query, params)
            for row in cursor.fetchall():
                yield {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "payload": json.loads(row["payload"] or "{}"),
                    "created_at": row["created_at"],
                }

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def get_default_store() -> SQLStore:
    """
    Convenience accessor used by scripts that only need a single store instance.
    """
    return SQLStore()
