"""Map rotation and definitions."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

_DATA_PATH = Path(__file__).parent / "data" / "maps.json"

@dataclass
class MapDef:
    id: str
    theme: str
    goals: List[str]


def load_maps() -> List[MapDef]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [MapDef(**m) for m in raw]
