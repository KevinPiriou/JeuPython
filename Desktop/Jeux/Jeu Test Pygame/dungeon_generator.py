# dungeon_generator.py
import random
import copy

class DungeonGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map_data = []
        self.secret_door = None

    def generate_map(self, num_rooms, min_room_size, max_room_size):
        """
        Génère un donjon sans objectif de couverture.
        Inclut un sas de spawn et une salle secrète.
        """
        max_attempts = 10000

        best_map_data = None
        best_rooms = []

        for _ in range(max_attempts):
            # 1) Initialiser en "tout mur"
            self.init_all_walls()

            # 2) Créer un sas 2×2
            spawn_sas = [(1, 1), (2, 1), (1, 2), (2, 2)]
            for (sx, sy) in spawn_sas:
                self.map_data[sy][sx]["is_wall"] = False

            # 3) Créer des salles
            rooms = self.create_random_rooms(num_rooms, min_room_size, max_room_size)

            # 4) Connecter les salles
            self.connect_rooms(rooms)

            # 5) Mettre les bords extérieurs en murs
            self.set_outer_walls()

            # 6) Mémoriser la meilleure tentative
            best_map_data = copy.deepcopy(self.map_data)
            best_rooms = rooms

            # Si la génération est réussie, on peut arrêter ici
            break

        # Après les tentatives, on garde la meilleure version
        self.map_data = best_map_data

        # 7) Marquer la dernière salle comme secrète
        if best_rooms:
            self.mark_secret_room(best_rooms[-1])

        # 8) Peupler la carte (ennemis / items)
        self.populate(best_rooms, spawn_sas)

        return self.map_data

    def init_all_walls(self):
        """
        Initialise la carte en "tout mur".
        """
        self.map_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = {
                    "is_wall": True,
                    "has_enemy": False,
                    "has_item": False,
                    "is_secret": False
                }
                row.append(cell)
            self.map_data.append(row)

    def create_random_rooms(self, num_rooms, min_size, max_size):
        """
        Crée des salles aléatoires rectangulaires, sans chevauchement.
        """
        rooms = []
        attempts = 0
        max_attempts = 100

        while len(rooms) < num_rooms and attempts < max_attempts:
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)

            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = (x, y, w, h)
            if not self.intersect(new_room, rooms):
                rooms.append(new_room)
                for ry in range(y, y + h):
                    for rx in range(x, x + w):
                        self.map_data[ry][rx]["is_wall"] = False

            attempts += 1

        return rooms

    def intersect(self, new_room, rooms):
        """
        Vérifie si une salle chevauche d'autres salles.
        """
        (x, y, w, h) = new_room
        for room in rooms:
            (rx, ry, rw, rh) = room
            if (x < rx + rw and x + w > rx and
                y < ry + rh and y + h > ry):
                return True
        return False

    def connect_rooms(self, rooms):
        """
        Connecte les salles par des couloirs en "L".
        """
        for i in range(len(rooms) - 1):
            (x1, y1, w1, h1) = rooms[i]
            (x2, y2, w2, h2) = rooms[i + 1]

            cx1 = x1 + w1 // 2
            cy1 = y1 + h1 // 2
            cx2 = x2 + w2 // 2
            cy2 = y2 + h2 // 2

            # Couloir horizontal
            if cx2 < cx1:
                start_x, end_x = cx2, cx1
            else:
                start_x, end_x = cx1, cx2
            for x in range(start_x, end_x + 1):
                self.map_data[cy1][x]["is_wall"] = False

            # Couloir vertical
            if cy2 < cy1:
                start_y, end_y = cy2, cy1
            else:
                start_y, end_y = cy1, cy2
            for y in range(start_y, end_y + 1):
                self.map_data[y][cx2]["is_wall"] = False

    def set_outer_walls(self):
        """
        Force des murs tout autour du donjon.
        """
        for x in range(self.width):
            self.map_data[0][x]["is_wall"] = True
            self.map_data[self.height - 1][x]["is_wall"] = True
        for y in range(self.height):
            self.map_data[y][0]["is_wall"] = True
            self.map_data[y][self.width - 1]["is_wall"] = True

    def mark_secret_room(self, room):
        """
        Marque une salle comme secrète et ferme sa porte.
        """
        (rx, ry, rw, rh) = room
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                self.map_data[y][x]["is_secret"] = True

        door_x = rx + rw // 2
        door_y = ry - 1
        if 0 <= door_x < self.width and 0 <= door_y < self.height:
            self.map_data[door_y][door_x]["is_wall"] = True
            self.secret_door = (door_x, door_y)

    def populate(self, rooms, spawn_sas):
        """
        Place des ennemis et des items dans les salles.
        """
        for (x, y, w, h) in rooms:
            # Ennemi
            for _ in range(3):
                rx = random.randint(x, x + w - 1)
                ry = random.randint(y, y + h - 1)
                if (rx, ry) in spawn_sas:
                    continue
                if not self.map_data[ry][rx]["is_wall"]:
                    self.map_data[ry][rx]["has_enemy"] = True
                    break

            # Item
            for _ in range(3):
                rx = random.randint(x, x + w - 1)
                ry = random.randint(y, y + h - 1)
                if (rx, ry) in spawn_sas:
                    continue
                if not self.map_data[ry][rx]["is_wall"]:
                    self.map_data[ry][rx]["has_item"] = True
                    break

def find_free_tile(map_data):
    """
    Trouve une tuile libre (non mur).
    """
    for y, row in enumerate(map_data):
        for x, cell in enumerate(row):
            if not cell["is_wall"]:
                return (x, y)
    return None
