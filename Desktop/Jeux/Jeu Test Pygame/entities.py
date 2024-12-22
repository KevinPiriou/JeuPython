# entities.py
import math

class Entity:
    def __init__(self, x, y, hp):
        self.x = x      # position en pixels
        self.y = y      # position en pixels
        self.hp = hp

    def is_alive(self):
        return self.hp > 0

class Player(Entity):
    def __init__(self, x, y, hp=100):
        super().__init__(x, y, hp)
        self.speed = 3
        self.damage = 10

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

    def attack(self, target):
        dist = math.hypot(target.x - self.x, target.y - self.y)
        if dist < 50:  # Portée d'attaque
            target.hp -= self.damage


class Enemy(Entity):
    def __init__(self, x, y, hp=50):
        super().__init__(x, y, hp)
        self.speed = 1.5
        self.damage = 5
        self.vision_range = 75  # champ de vision en pixels

    def update(self, player, map_data, offset_x, offset_y, tile_size):
        """
        - Vérifie si le joueur est dans le champ de vision.
        - Se déplace vers lui si c'est le cas (en évitant de traverser les murs).
        - Attaque le joueur si assez proche.
        """
        if not self.is_alive():
            return

        # Distance au joueur
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        # Si le joueur est hors vision, on ne bouge pas
        if dist > self.vision_range:
            return

        # Normaliser dx, dy
        if dist != 0:
            dx /= dist
            dy /= dist

        # Mémoriser l'ancienne position
        old_x = self.x
        old_y = self.y

        # Déplacement
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Vérifier si on traverse un mur
        tile_x = int((self.x - offset_x) // tile_size)
        tile_y = int((self.y - offset_y) // tile_size)

        height = len(map_data)
        width = len(map_data[0]) if height > 0 else 0

        # Collision
        if 0 <= tile_x < width and 0 <= tile_y < height:
            if map_data[tile_y][tile_x]["is_wall"]:
                # on annule le déplacement
                self.x = old_x
                self.y = old_y
        else:
            # en dehors de la map
            self.x = old_x
            self.y = old_y

        # Si on est très proche du joueur, on lui inflige des dégâts
        if dist < 40:
            player.hp -= self.damage
