import unittest
from .game import SpriteGame

class TestSpriteGame(unittest.TestCase):
    def test_register_and_initial_sprite(self):
        game = SpriteGame()
        user = game.register_user("alice")
        sprite = game.give_initial_sprite(user)
        self.assertEqual(user.sprites[0], sprite)
        self.assertEqual(sprite.name, "alice's Sprite")

    def test_lorekeeper(self):
        game = SpriteGame()
        self.assertIn("Ancient tales", game.talk_to_lorekeeper())

    def test_battle_progression(self):
        game = SpriteGame()
        user = game.register_user("bob")
        sprite = game.give_initial_sprite(user)
        starting_power = sprite.total_power
        result = game.battle(user)
        self.assertIn("defeated", result)
        self.assertGreater(sprite.total_power, starting_power)
        # Enemy level should have increased
        self.assertEqual(game.enemy_level, 2)

    def test_customization_and_prize(self):
        game = SpriteGame()
        user = game.register_user("cara")
        sprite = game.give_initial_sprite(user)
        msg = game.customize_avatar(user, "red", "hat")
        self.assertIn("red", msg)
        self.assertEqual(sprite.appearance.color, "red")

        # advance battles to unlock an epic prize
        for _ in range(4):
            game.battle(user)
        result = game.battle(user)
        self.assertIn("Epic", result)
        self.assertTrue(any(p.rarity == "Epic" for p in sprite.prizes))

    def test_contributions_and_ranking(self):
        game = SpriteGame()
        # create many users with ascending token counts
        for i in range(105):
            u = game.register_user(f"user{i}")
            game.award_tokens(u, i)

        top_user = game.users["user104"]
        low_user = game.users["user0"]

        self.assertEqual(top_user.rank_code, 1)
        self.assertIsNone(low_user.rank_code)

        game.record_contribution(top_user, 10)
        game.record_referral_contribution(top_user, 5)
        self.assertEqual(top_user.contribution, 10)
        self.assertEqual(top_user.referral_contribution, 5)

if __name__ == "__main__":
    unittest.main()

