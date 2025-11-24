"""
Lightweight configuration loader for Codex runtime scripts.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


CONFIG_PATH = Path(__file__).resolve().parent / "global_config.yaml"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """
    Load the global configuration file. The file is authored as JSON,
    which is also valid YAML, making it easy to parse without extra deps.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file at {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_data_path() -> Path:
    """
    Resolve the path to the runtime data directory described in the config.
    """
    config = load_config()
    data_dir = config.get("runtime", {}).get("data_dir", "data")
    path = CONFIG_PATH.parent.parent / data_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_database_path() -> Path:
    """
    Compute the sqlite database path used across the runtime components.
    """
    config = load_config()
    db_name = config.get("runtime", {}).get("db_file", "codex.db")
    return get_data_path() / db_name
