"""Simplified game skeleton for NFT-like sprites."""
from typing import Dict, List, Optional
from .models import (
    Sprite,
    Minion,
    Equipment,
    LoreKeeper,
    Enemy,
    Prize,
)
from .user import User
from .mcp_client import MCPClient

class SpriteGame:
    def __init__(self, mcp_client: Optional[MCPClient] = None):
        self.users: Dict[str, User] = {}
        # Stationary NPC known for telling stories
        self.lorekeeper = LoreKeeper()
        self.enemy_level = 1
        self.mcp = mcp_client or MCPClient()
        # register the lorekeeper with the MCP
        self.mcp.register_npc(self.lorekeeper.name, {"location": self.lorekeeper.location})

    def _update_rankings(self) -> None:
        """Assign rank codes to the top 100 users by token balance."""
        sorted_users: List[User] = sorted(
            self.users.values(), key=lambda u: u.tokens, reverse=True
        )
        for idx, user in enumerate(sorted_users):
            if idx < 100:
                user.rank_code = idx + 1
            else:
                user.rank_code = None

    def register_user(self, username: str) -> User:
        user = User(username=username)
        self.users[username] = user
        self._update_rankings()
        return user

    def give_initial_sprite(self, user: User) -> Sprite:
        sprite = Sprite(name=f"{user.username}'s Sprite", classes=["Warrior", "Mage", "Rogue"])
        user.give_sprite(sprite)
        self.mcp.register_npc(sprite.sprite_id, {"owner": user.username, "classes": sprite.classes})
        return sprite

    def award_tokens(self, user: User, amount: int) -> None:
        user.add_tokens(amount)
        self._update_rankings()

    def record_contribution(self, user: User, amount: int) -> None:
        user.add_contribution(amount)

    def record_referral_contribution(self, user: User, amount: int) -> None:
        user.add_referral_contribution(amount)

    def get_rank_code(self, user: User) -> Optional[int]:
        return user.rank_code

    def talk_to_lorekeeper(self) -> str:
        """Return lore from the stationary NPC."""
        lore = self.lorekeeper.speak()
        self.mcp.trigger_event("lore", {"npc": self.lorekeeper.name})
        return lore

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
        self.mcp.trigger_event(
            "customize_avatar",
            {"sprite": sprite.sprite_id, "color": color, "accessory": accessory},
        )
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
            self.award_tokens(user, 10 * self.enemy_level)
            self.mcp.trigger_event(
                "battle",
                {
                    "sprite": sprite.sprite_id,
                    "enemy": enemy.name,
                    "result": "win",
                },
            )
            return (
                f"{sprite.name} defeated the {enemy.name}! "
                f"Gained {new_item.name}.{prize_msg}"
            )
        else:
            # Player loses but enemy still grows a bit
            self.enemy_level += 1
            self.mcp.trigger_event(
                "battle",
                {
                    "sprite": sprite.sprite_id,
                    "enemy": enemy.name,
                    "result": "loss",
                },
            )
            return f"{sprite.name} was defeated by the {enemy.name}."

