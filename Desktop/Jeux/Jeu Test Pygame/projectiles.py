import pymunk
import math

# Constantes de collision
PROJECTILE_COLLISION_TYPE = 1
ENEMY_COLLISION_TYPE = 2
WALL_COLLISION_TYPE = 3

class Projectile:
    def __init__(self, body, shape):
        self.body = body
        self.shape = shape

def setup_pymunk_space():
    """
    Configure et retourne un espace Pymunk pour la simulation physique.
    """
    space = pymunk.Space()
    space.gravity = (0, 0)
    return space

def add_projectile(space, x, y, target_x, target_y):
    """
    Crée un projectile se déplaçant de (x, y) vers (target_x, target_y).
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

    speed = 400  # Vitesse du projectile
    body.velocity = (dx * speed, dy * speed)

    space.add(body, shape)
    return Projectile(body, shape)

def add_wall(space, x, y, width, height):
    """
    Ajoute un mur statique à l'espace.
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (x, y)

    shape = pymunk.Poly.create_box(body, (width, height))
    shape.collision_type = WALL_COLLISION_TYPE

    space.add(body, shape)
    return shape

def register_collision_handlers(space, enemies):
    """
    Configure les gestionnaires de collision pour les projectiles et les ennemis.
    """
    def projectile_hits_enemy(arbiter, space, data):
        """
        Gère la collision entre un projectile et un ennemi.
        """
        proj_shape, enemy_shape = arbiter.shapes
        enemy = enemy_shape.user_data

        # Réduire les points de vie de l'ennemi
        if enemy is not None:
            enemy.hp -= 20
            print(f"Ennemi touché ! HP restant : {enemy.hp}")

        # Supprimer le projectile
        space.remove(proj_shape.body, proj_shape)
        print("Projectile supprimé après collision avec un ennemi.")

        return False  # Empêche tout rebond ou effet supplémentaire

    handler = space.add_collision_handler(PROJECTILE_COLLISION_TYPE, ENEMY_COLLISION_TYPE)
    handler.begin = projectile_hits_enemy

    def projectile_hits_wall(arbiter, space, data):
        """
        Gère la collision entre un projectile et un mur.
        """
        proj_shape = arbiter.shapes[0]

        # Supprimer le projectile
        space.remove(proj_shape.body, proj_shape)
        print("Projectile supprimé après collision avec un mur.")

        return False  # Empêche tout rebond ou effet supplémentaire


    wall_handler = space.add_collision_handler(PROJECTILE_COLLISION_TYPE, WALL_COLLISION_TYPE)
    wall_handler.begin = projectile_hits_wall

