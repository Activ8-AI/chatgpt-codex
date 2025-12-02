"""
Ledger orchestration helpers that sit on top of the SQL store.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from configs import load_config
from memory.sql_store.sql_store import SQLStore, get_default_store


class CustodianLedger:
    """
    Provides structured helpers for writing well-formed ledger entries.
    """

    def __init__(self, store: Optional[SQLStore] = None) -> None:
        self.store = store or get_default_store()
        autonomy = load_config().get("autonomy", {})
        self.loop_label = autonomy.get("loop_label", "AUTONOMY_LOOP")

    def record(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> int:
        enriched = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            **(payload or {}),
        }
        return self.store.record_event(event_type, enriched)

    def record_autonomy_loop(self, step: str, details: Optional[Dict[str, Any]] = None) -> int:
        payload = {
            "step": step,
            **(details or {}),
        }
        return self.record(self.loop_label, payload)

    def latest(self, event_type: Optional[str] = None, limit: int = 25) -> Iterable[Dict[str, Any]]:
        return self.store.fetch_events(event_type=event_type, limit=limit)
