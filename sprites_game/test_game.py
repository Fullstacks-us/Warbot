import unittest
from .game import SpriteGame

class TestSpriteGame(unittest.TestCase):
    def test_register_and_initial_sprite(self):
        game = SpriteGame()
        user = game.register_user("alice")
        sprite = game.give_initial_sprite(user)
        self.assertEqual(user.sprites[0], sprite)
        self.assertEqual(sprite.name, "alice's Sprite")

if __name__ == "__main__":
    unittest.main()
