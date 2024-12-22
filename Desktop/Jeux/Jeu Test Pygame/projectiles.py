# projectiles.py

import pymunk
import math

PROJECTILE_COLLISION_TYPE = 1
ENEMY_COLLISION_TYPE = 2
WALL_COLLISION_TYPE = 3  # on peut s'en servir si on veut gérer collisions murs

class Projectile:
    def __init__(self, body, shape):
        self.body = body
        self.shape = shape

def setup_pymunk_space():
    space = pymunk.Space()
    space.gravity = (0, 0)
    return space

def add_projectile(space, x, y, target_x, target_y):
    """
    Crée un projectile se déplaçant de (x,y) vers (target_x, target_y).
    """
    body = pymunk.Body(mass=1, moment=10)
    body.position = (x, y)
    shape = pymunk.Circle(body, 5)
    shape.collision_type = PROJECTILE_COLLISION_TYPE
    shape.friction = 0.5
    shape.elasticity = 0.0

    # Calcul direction
    dx = target_x - x
    dy = target_y - y
    dist = math.hypot(dx, dy)
    if dist != 0:
        dx /= dist
        dy /= dist

    speed = 400
    body.velocity = (dx * speed, dy * speed)

    space.add(body, shape)
    return Projectile(body, shape)

def register_collision_handlers(space, enemies):
    """
    Gère la collision projectile/ennemi :
     - Inflige des dégâts
     - Détruit le projectile
    """

    def projectile_hits_enemy(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        # on identifie qui est le projectile et qui est l'ennemi
        proj_shape = None
        enemy_shape = None
        if shape_a.collision_type == PROJECTILE_COLLISION_TYPE:
            proj_shape = shape_a
            enemy_shape = shape_b
        else:
            proj_shape = shape_b
            enemy_shape = shape_a

        # Retrouver l'ennemi correspondant
        # On peut stocker "enemy" dans enemy_shape.user_data
        enemy = enemy_shape.user_data
        if enemy is not None:
            # on inflige des dégâts
            enemy.hp -= 20  # par exemple

        # On supprime le projectile du space
        space.remove(proj_shape.body, proj_shape)

        return False  # pas de rebond

    handler = space.add_collision_handler(PROJECTILE_COLLISION_TYPE, ENEMY_COLLISION_TYPE)
    handler.begin = projectile_hits_enemy
