from dataclasses import dataclass, field
from typing import List
from .models import Sprite

@dataclass
class User:
    username: str
    sprites: List[Sprite] = field(default_factory=list)

    def give_sprite(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)
