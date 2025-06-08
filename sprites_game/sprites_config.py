"""Load sprite personalities."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

_DATA_PATH = Path(__file__).parent / "data" / "sprites.json"

@dataclass
class SpritePersona:
    id: str
    role: str
    dialog: List[str]


def load_sprites() -> List[SpritePersona]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [SpritePersona(**s) for s in raw]
