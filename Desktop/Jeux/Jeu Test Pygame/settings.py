
# settings.py
import random
# Définition des couleurs sous forme de tuples RGB
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (130, 130, 130)

# Couleurs du jeu
MUR_COLOR = BLACK       # Couleur des murs
TILE_COLOR = GRAY     # Couleur des tuiles libres
PLAYER_COLOR = BLUE    # Couleur du joueur
ENEMY_COLOR = RED      # Couleur des ennemis
ITEM_COLOR = YELLOW    # Couleur des items
PROJECTILE_COLOR = MAGENTA  # Couleur des projectiles
ROOM_COLORS = {
    "None": GRAY,       # Par défaut
    "Normal": GRAY,
    "Spawn": CYAN,
    "Boss": RED,
    "Treasure": YELLOW,
    "Trap": ORANGE,
    "Secret": PURPLE,
}

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

TILE_SIZE = 51

# Marges pour centrer la map
MARGIN_X = 5
MARGIN_Y = 5

# Hauteur du HUD
HUD_HEIGHT = 92

# Paramètres de génération de salles
NUM_ROOMS = random.randint(4, 8)
MIN_ROOM_SIZE = 3
MAX_ROOM_SIZE = 8

# Rayon de lock automatique
LOCK_RANGE = 75

# Cooldown en millisecondes entre deux tirs
SHOOT_COOLDOWN_MS = 750
