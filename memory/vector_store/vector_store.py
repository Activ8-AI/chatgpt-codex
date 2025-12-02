"""
Toy vector store used for experimentation during Codex local runs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from configs import get_data_path


class VectorStore:
    """
    Extremely small persistence layer that keeps vectors in a JSON file.
    """

    def __init__(self, filename: str = "vectors.json") -> None:
        self.path = get_data_path() / filename
        if not self.path.exists():
            self._save({})

    def _load(self) -> Dict[str, List[float]]:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, payload: Dict[str, List[float]]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def add(self, key: str, vector: Iterable[float]) -> None:
        data = self._load()
        data[key] = list(vector)
        self._save(data)

    def get(self, key: str) -> List[float]:
        data = self._load()
        return data[key]

    def items(self) -> Dict[str, List[float]]:
        return self._load()
