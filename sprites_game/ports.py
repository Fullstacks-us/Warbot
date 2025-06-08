"""Load and access port definitions."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

_DATA_PATH = Path(__file__).parent / "data" / "ports.json"

@dataclass
class Port:
    id: str
    type: str
    description: str


def load_ports() -> List[Port]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Port(**p) for p in raw]
