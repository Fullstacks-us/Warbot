"""Simplified game skeleton for NFT-like sprites."""
from typing import Dict
from .models import Sprite, Minion, Equipment, LoreKeeper
from .user import User

class SpriteGame:
    def __init__(self):
        self.users: Dict[str, User] = {}
        # Stationary NPC known for telling stories
        self.lorekeeper = LoreKeeper()

    def register_user(self, username: str) -> User:
        user = User(username=username)
        self.users[username] = user
        return user

    def give_initial_sprite(self, user: User) -> Sprite:
        sprite = Sprite(name=f"{user.username}'s Sprite", classes=["Warrior", "Mage", "Rogue"])
        user.give_sprite(sprite)
        return sprite

    def talk_to_lorekeeper(self) -> str:
        """Return lore from the stationary NPC."""
        return self.lorekeeper.speak()

    def wander(self, user: User) -> str:
        """Sprites wander and may request attention."""
        if not user.sprites:
            return "No sprites yet."
        sprite = user.sprites[0]
        return f"{sprite.name} wanders around and looks curious."
