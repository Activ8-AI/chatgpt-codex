"""
Agent activation helpers that coordinate relays and ledger access.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from custody.custodian_ledger import CustodianLedger
from relay.notion_relay import NotionRelay
from relay.slack_signal import SlackSignal
from relay.teamwork_sink import TeamworkSink


class AgentHub:
    def __init__(self, ledger: Optional[CustodianLedger] = None) -> None:
        self.ledger = ledger or CustodianLedger()
        self.notion = NotionRelay()
        self.slack = SlackSignal()
        self.teamwork = TeamworkSink()

    def activate(self, task_summary: str) -> Dict[str, Any]:
        """
        Fan the task summary out to the relays and note the results.
        """
        payload = {"task": task_summary}
        responses = {
            "notion": self.notion.send(payload),
            "slack": self.slack.send(payload),
            "teamwork": self.teamwork.send(payload),
        }
        self.ledger.record(
            "AGENT_ACTIVATION",
            {
                "task": task_summary,
                "responses": responses,
            },
        )
        return responses
