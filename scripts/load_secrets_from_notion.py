"""
Stub script that simulates pulling secrets from Notion.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs import get_data_path


def main() -> None:
    secrets_path = get_data_path() / "secrets_state.json"
    secrets_payload = {
        "source": "notion",
        "loaded_at": datetime.now(tz=timezone.utc).isoformat(),
        "values": {
            "OPENAI_API_KEY": "stub-value",
            "SLACK_TOKEN": "stub-value",
        },
    }
    secrets_path.write_text(json.dumps(secrets_payload, indent=2), encoding="utf-8")
    print(f"[codex] Stored stub secrets at {secrets_path}")


if __name__ == "__main__":
    main()
