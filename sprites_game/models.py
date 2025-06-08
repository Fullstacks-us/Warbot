from dataclasses import dataclass, field
from typing import List, Dict
import uuid

@dataclass
class Equipment:
    name: str
    bonuses: Dict[str, int] = field(default_factory=dict)

@dataclass
class Minion:
    name: str
    power: int

@dataclass
class Sprite:
    """Represents an NFT-like sprite."""
    sprite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unnamed"
    classes: List[str] = field(default_factory=list)
    minions: List[Minion] = field(default_factory=list)
    equipment: List[Equipment] = field(default_factory=list)

    def add_minion(self, minion: Minion) -> None:
        self.minions.append(minion)

    def add_equipment(self, equip: Equipment) -> None:
        self.equipment.append(equip)


@dataclass
class LoreKeeper:
    """Stationary NPC that shares lore."""
    name: str = "Lorekeeper"
    location: str = "Town Square"
    lore: str = (
        "Ancient tales whisper of heroes and sprites alike."
    )

    def speak(self) -> str:
        return self.lore
