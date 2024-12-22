# entities.py
import math

class Entity:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.hp = hp

    def is_alive(self):
        return self.hp > 0


class Player(Entity):
    def __init__(self, x, y, hp=100):
        super().__init__(x, y, hp)
        self.speed = 3
        self.damage = 10
        self.last_shot_time = 0  # on l'ajoute pour gérer le cooldown

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

    def attack(self, target):
        dist = math.hypot(target.x - self.x, target.y - self.y)
        if dist < 50:  # portée d'attaque melee
            target.hp -= self.damage


class Enemy(Entity):
    def __init__(self, x, y, hp=50):
        super().__init__(x, y, hp)
        self.speed = 2
        self.damage = 5
        self.vision_range = 200

    def update(self, player, map_data, offset_x, offset_y, tile_size):
        if not self.is_alive():
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.vision_range:
            return

        if dist != 0:
            dx /= dist
            dy /= dist

        old_x, old_y = self.x, self.y
        self.x += dx * self.speed
        self.y += dy * self.speed

        tile_x = int((self.x - offset_x) // tile_size)
        tile_y = int((self.y - offset_y) // tile_size)

        height = len(map_data)
        width = len(map_data[0]) if height > 0 else 0

        if 0 <= tile_x < width and 0 <= tile_y < height:
            if map_data[tile_y][tile_x]["is_wall"]:
                self.x, self.y = old_x, old_y
        else:
            self.x, self.y = old_x, old_y

        if dist < 40:
            player.hp -= self.damage
