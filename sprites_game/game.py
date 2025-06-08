"""Simplified game skeleton for NFT-like sprites."""
from typing import Dict
from .models import (
    Sprite,
    Minion,
    Equipment,
    LoreKeeper,
    Enemy,
    Prize,
)
from .user import User

class SpriteGame:
    def __init__(self):
        self.users: Dict[str, User] = {}
        # Stationary NPC known for telling stories
        self.lorekeeper = LoreKeeper()
        self.enemy_level = 1

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

    def customize_avatar(self, user: User, color: str, accessory: str) -> str:
        """Allow simple customization of a sprite's look."""
        if not user.sprites:
            return "No sprites yet."
        sprite = user.sprites[0]
        sprite.appearance.color = color
        sprite.appearance.accessory = accessory
        return f"{sprite.name} is now {color} with {accessory}."

    def battle(self, user: User) -> str:
        """Simple battle mechanic where sprites and enemies grow stronger."""
        if not user.sprites:
            return "No sprites yet."

        sprite = user.sprites[0]
        enemy = Enemy(name="Goblin", level=self.enemy_level)

        if sprite.total_power >= enemy.power:
            # Player wins, reward equipment and increase difficulty
            new_item = Equipment(
                name=f"Victory Gear Lv{self.enemy_level}",
                bonuses={"power": self.enemy_level}
            )
            sprite.add_equipment(new_item)
            sprite.base_power += 1
            prize_msg = ""
            if self.enemy_level % 5 == 0:
                prize = Prize(name="Epic Chest", rarity="Epic")
                sprite.prizes.append(prize)
                prize_msg = f" Found {prize.name}!"
            self.enemy_level += 1
            return (
                f"{sprite.name} defeated the {enemy.name}! "
                f"Gained {new_item.name}.{prize_msg}"
            )
        else:
            # Player loses but enemy still grows a bit
            self.enemy_level += 1
            return f"{sprite.name} was defeated by the {enemy.name}."

