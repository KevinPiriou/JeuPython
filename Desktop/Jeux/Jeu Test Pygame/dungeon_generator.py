# dungeon_generator.py

import random
import copy

class DungeonGenerator:
    def __init__(self, width, height):
        """
        :param width: largeur du donjon en tuiles
        :param height: hauteur du donjon en tuiles
        """
        self.width = width
        self.height = height
        self.map_data = []

    def generate_map(self, num_rooms, min_room_size, max_room_size):
        """
        Génère un donjon dont le ratio de tuiles libres est entre 60% et 90%.
        Recommence plusieurs fois si besoin (max_attempts).
        """
        coverage_min = 0.9
        coverage_max = 0.99
        coverage_target = (coverage_min + coverage_max) / 2.5
        max_attempts = 1000

        best_map_data = None
        best_coverage_diff = 1.0  # 1.0 = 100%

        for _ in range(max_attempts):
            # 1) Initialiser en "tout mur"
            self.init_all_walls()

            # 2) Créer un certain nombre de salles
            rooms = self.create_random_rooms(num_rooms, min_room_size, max_room_size)

            # 3) Connecter les salles
            self.connect_rooms(rooms)

            # 4) Mettre les bords en murs
            self.set_outer_walls()

            # 5) Mesurer la couverture (tuiles libres vs total)
            coverage = self.measure_coverage()

            # Calculer la différence absolue par rapport à la "cible" (0.75)
            coverage_diff = abs(coverage - coverage_target)

            # Si c'est la meilleure tentative jusqu'ici, on la sauvegarde
            if coverage_diff < best_coverage_diff:
                best_coverage_diff = coverage_diff
                best_map_data = copy.deepcopy(self.map_data)
                best_rooms = rooms

            # Si on est déjà dans la fourchette, on arrête
            if coverage_min <= coverage <= coverage_max:
                break

        # Après les tentatives, on garde la meilleure map_data trouvée
        self.map_data = best_map_data

        # Ajout d'ennemis et items dans la carte
        # (Pour éviter de peupler plusieurs fois)
        self.populate(best_rooms)

        return self.map_data

    def init_all_walls(self):
        """
        Initialise self.map_data en "tout mur".
        """
        self.map_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = {
                    "is_wall": True,
                    "has_enemy": False,
                    "has_item": False
                }
                row.append(cell)
            self.map_data.append(row)

    def create_random_rooms(self, num_rooms, min_size, max_size):
        """
        Crée un certain nombre de salles aléatoires (rectangulaires).
        Les salles sont creusées (is_wall=False).
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

            # Vérifie pas de chevauchement
            if not self.intersect(new_room, rooms):
                rooms.append(new_room)
                # Creuse la salle
                for ry in range(y, y + h):
                    for rx in range(x, x + w):
                        self.map_data[ry][rx]["is_wall"] = False

            attempts += 1

        return rooms

    def intersect(self, new_room, rooms):
        """
        Vérifie si la salle new_room chevauche d'autres salles.
        new_room = (x, y, w, h)
        rooms = liste de (x, y, w, h)
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
        Connecte les salles dans l'ordre : la salle i reliée à la salle i+1
        par un couloir en L.
        """
        for i in range(len(rooms) - 1):
            (x1, y1, w1, h1) = rooms[i]
            (x2, y2, w2, h2) = rooms[i+1]

            cx1 = x1 + w1//2
            cy1 = y1 + h1//2
            cx2 = x2 + w2//2
            cy2 = y2 + h2//2

            # Couloir horizontal
            if cx2 < cx1:
                start_x, end_x = cx2, cx1
            else:
                start_x, end_x = cx1, cx2
            for x in range(start_x, end_x+1):
                self.map_data[cy1][x]["is_wall"] = False

            # Couloir vertical
            if cy2 < cy1:
                start_y, end_y = cy2, cy1
            else:
                start_y, end_y = cy1, cy2
            for y in range(start_y, end_y+1):
                self.map_data[y][cx2]["is_wall"] = False

    def set_outer_walls(self):
        """
        Force des murs tout autour du donjon.
        """
        for x in range(self.width):
            self.map_data[0][x]["is_wall"] = True
            self.map_data[self.height-1][x]["is_wall"] = True

        for y in range(self.height):
            self.map_data[y][0]["is_wall"] = True
            self.map_data[y][self.width-1]["is_wall"] = True

    def measure_coverage(self):
        """
        Calcule le ratio de tuiles libres (False) par rapport au total.
        """
        total_cells = self.width * self.height
        free_cells = 0
        for row in self.map_data:
            for cell in row:
                if cell["is_wall"] == False:
                    free_cells += 1
        coverage = free_cells / total_cells
        return coverage

    def populate(self, rooms):
        """
        Place des ennemis/items dans les salles (comme avant).
        """
        for (x, y, w, h) in rooms:
            # Ennemi
            for _ in range(3):
                rx = random.randint(x, x + w - 1)
                ry = random.randint(y, y + h - 1)
                if not self.map_data[ry][rx]["is_wall"]:
                    self.map_data[ry][rx]["has_enemy"] = True
                    break

            # Item
            for _ in range(3):
                rx = random.randint(x, x + w - 1)
                ry = random.randint(y, y + h - 1)
                if not self.map_data[ry][rx]["is_wall"]:
                    self.map_data[ry][rx]["has_item"] = True
                    break


def find_free_tile(map_data):
    """
    Parcourt la map pour trouver la première tuile libre (is_wall=False).
    Retourne (x, y) ou None si pas trouvé.
    """
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0

    for y in range(height):
        for x in range(width):
            if not map_data[y][x]["is_wall"]:
                return (x, y)
    return None
