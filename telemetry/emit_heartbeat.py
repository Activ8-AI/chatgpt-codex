"""
Heartbeat utilities that plug into the FastAPI relay and scripts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from custody.custodian_ledger import CustodianLedger


class HeartbeatEmitter:
    """
    Emits routine heartbeat events and records them to the ledger.
    """

    def __init__(self, ledger: Optional[CustodianLedger] = None) -> None:
        self.ledger = ledger or CustodianLedger()

    def emit(self, source: str = "relay") -> Dict[str, str]:
        payload = {
            "source": source,
            "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self.ledger.record("HEARTBEAT", payload)
        return payload
