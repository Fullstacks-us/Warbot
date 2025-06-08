from dataclasses import dataclass, field
from typing import List, Dict
import uuid


@dataclass
class Appearance:
    """Simple avatar customization."""
    color: str = "gray"
    accessory: str = ""


@dataclass
class Prize:
    name: str
    rarity: str = "Common"

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
    prizes: List[Prize] = field(default_factory=list)
    appearance: Appearance = field(default_factory=Appearance)
    base_power: int = 5

    def add_minion(self, minion: Minion) -> None:
        self.minions.append(minion)

    def add_equipment(self, equip: Equipment) -> None:
        self.equipment.append(equip)

    @property
    def total_power(self) -> int:
        """Compute the sprite's combat power."""
        power = self.base_power
        power += sum(m.power for m in self.minions)
        for eq in self.equipment:
            power += eq.bonuses.get("power", 0)
        return power


@dataclass
class Enemy:
    name: str
    level: int
    base_power: int = 3

    @property
    def power(self) -> int:
        return self.base_power + self.level


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

