from dataclasses import dataclass, field
from typing import List, Optional
from .models import Sprite

@dataclass
class User:
    username: str
    sprites: List[Sprite] = field(default_factory=list)
    tokens: int = 0
    contribution: int = 0
    referral_contribution: int = 0
    rank_code: Optional[int] = None

    def give_sprite(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)

    def add_tokens(self, amount: int) -> None:
        self.tokens += amount

    def add_contribution(self, amount: int) -> None:
        self.contribution += amount

    def add_referral_contribution(self, amount: int) -> None:
        self.referral_contribution += amount
