import unittest
from entities import *
from inventory import *
from dungeon_generator import *
from projectiles import *
import math

class TestEntities(unittest.TestCase):
    def test_player_movement(self):
        player = Player(0, 0)
        player.move(1, 0)
        self.assertEqual((player.x, player.y), (3, 0))

    def test_player_attack(self):
        player = Player(0, 0)
        enemy = Enemy(10, 0)
        player.attack(enemy)
        self.assertEqual(enemy.hp, 40)

    def test_enemy_detection_range(self):
        player = Player(0, 0)
        enemy = Enemy(250, 0)  # L'ennemi est hors de portée
        map_data = [[{"is_wall": False} for _ in range(10)] for _ in range(10)]

        # Mise à jour de l'ennemi
        enemy.update(player, map_data, 0, 0, 1)

        # Vérifiez qu'il ne bouge pas hors de portée
        self.assertEqual((enemy.x, enemy.y), (250, 0), "L'ennemi a bougé malgré la portée insuffisante.")

    def test_enemy_moves_when_player_in_range(self):
        player = Player(0, 0)
        enemy = Enemy(50, 0)
        enemy.vision_range = 100  # Assurez-vous que l'ennemi peut détecter le joueur
        map_data = [[{"is_wall": False} for _ in range(10)] for _ in range(10)]  # Carte sans murs

        # Mise à jour de l'ennemi
        enemy.update(player, map_data, 0, 0, 1)

        # Vérifiez que l'ennemi a bougé
        self.assertNotEqual((enemy.x, enemy.y), (50, 0), "L'ennemi ne s'est pas déplacé malgré la proximité du joueur.")

class TestInventory(unittest.TestCase):
    def test_add_item(self):
        inventory = Inventory()
        potion = Item("Potion", "heal", 20)
        inventory.add_item(potion)
        self.assertEqual(len(inventory.items), 1)

    def test_use_item_out_of_index(self):
        player = Player(0, 0, hp=50)
        inventory = Inventory()
        with self.assertRaises(IndexError):
         inventory.use_item(0, player)

    def test_use_item(self):
        player = Player(0, 0, hp=50)
        inventory = Inventory()
        potion = Item("Potion", "heal", 20)
        inventory.add_item(potion)
        inventory.use_item(0, player)
        self.assertEqual(player.hp, 70)
        self.assertEqual(len(inventory.items), 0)

class TestDungeonGenerator(unittest.TestCase):
    def test_generate_map(self):
        generator = DungeonGenerator(10, 10)
        map_data = generator.generate_map(5, 3, 5)
        self.assertIsNotNone(map_data)
        non_wall_count = sum(
            1 for row in map_data for cell in row if not cell["is_wall"]
        )
        self.assertGreater(non_wall_count, 0)
    def test_room_types_in_map(self):
     generator = DungeonGenerator(20, 20)
     map_data = generator.generate_map(5, 3, 5)
     room_types = {cell["room_type"] for row in map_data for cell in row}
     self.assertIn("Spawn", room_types)
     self.assertIn("Boss", room_types)

class TestProjectiles(unittest.TestCase):
    def test_projectile_creation(self):
        space = setup_pymunk_space()
        projectile = add_projectile(space, 0, 0, 100, 0)
        self.assertAlmostEqual(projectile.body.velocity.x, 400)
        self.assertAlmostEqual(projectile.body.velocity.y, 0)
    
    def test_projectile_hits_enemy(self):
        space = setup_pymunk_space()
        enemy = Enemy(100, 100)
        shape = pymunk.Circle(pymunk.Body(), 10)
        shape.user_data = enemy  # Associe l'ennemi à sa forme

        # Simule une collision
        projectile = add_projectile(space, 0, 0, 100, 100)
        handler = space.add_collision_handler(PROJECTILE_COLLISION_TYPE, ENEMY_COLLISION_TYPE)
        handler.begin(projectile, shape, None)

        # Vérifiez que l'ennemi a subi des dégâts
        self.assertEqual(enemy.hp, 30)  # Supposez des dégâts de 20


if __name__ == "__main__":
    unittest.main()
