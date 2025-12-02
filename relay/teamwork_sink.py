"""
Teamwork sink stub that archives payloads for auditing.
"""
from __future__ import annotations

from typing import Any, Dict


class TeamworkSink:
    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "destination": "teamwork",
            "payload": payload,
            "status": "archived",
        }
