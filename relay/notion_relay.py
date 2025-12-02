"""
Stub relay that simulates sending updates to Notion.
"""
from __future__ import annotations

from typing import Any, Dict


class NotionRelay:
    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # In lieu of a real integration, just mirror the payload.
        return {
            "destination": "notion",
            "payload": payload,
            "status": "queued",
        }
