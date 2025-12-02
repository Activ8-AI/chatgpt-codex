"""
Slack relay stub that returns a structured acknowledgement.
"""
from __future__ import annotations

from typing import Any, Dict


class SlackSignal:
    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "destination": "slack",
            "payload": payload,
            "status": "delivered",
        }
