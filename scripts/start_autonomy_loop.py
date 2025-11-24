"""
Simple autonomy loop that records activity to the ledger.
"""
from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_hub.activate import AgentHub
from configs import load_config
from custody.custodian_ledger import CustodianLedger


class AutonomyLoop:
    def __init__(self) -> None:
        config = load_config()
        self.interval = int(config.get("autonomy", {}).get("loop_interval_seconds", 5))
        self.ledger = CustodianLedger()
        self.agent_hub = AgentHub(self.ledger)
        self._running = True

    def _handle_signal(self, *_: object) -> None:
        self._running = False

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        print("[codex] Autonomy loop online. Press Ctrl+C to stop.")
        cycle = 0
        while self._running:
            cycle += 1
            summary = f"Cycle {cycle}"
            self.ledger.record_autonomy_loop(
                step=summary,
                details={"cycle": cycle},
            )
            responses = self.agent_hub.activate(task_summary=summary)
            print(f"[codex] Recorded {summary}. Relays: {list(responses.keys())}")
            time.sleep(self.interval)
        print("[codex] Autonomy loop shutting down gracefully.")


def main() -> None:
    AutonomyLoop().run()


if __name__ == "__main__":
    main()
