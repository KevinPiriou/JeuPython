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
        Génère un donjon avec sas de spawn et possibilité de salle secrète.
        """
        max_attempts = 10000

        best_map_data = None
        best_rooms = []

        for _ in range(max_attempts):
            self.init_all_walls()

            spawn_sas = [(1, 1), (2, 1), (1, 2), (2, 2)]
            for (sx, sy) in spawn_sas:
                self.map_data[sy][sx]["is_wall"] = False

            rooms = self.create_random_rooms(num_rooms, min_room_size, max_room_size)

            self.connect_rooms(rooms)
            self.connect_spawn_to_first_room(spawn_sas, rooms)
            self.add_secret_room(rooms)
            self.assign_room_types(rooms)
            self.set_outer_walls()
            

            best_map_data = copy.deepcopy(self.map_data)
            best_rooms = rooms
            break

        self.map_data = best_map_data
        self.populate(best_rooms, spawn_sas)
        return self.map_data
    def assign_room_types(self, rooms):
        """
        Attribue des types aux salles : Normal, Spawn, Boss, Treasure, Trap, Secret.
        """
        for i, room in enumerate(rooms):
            room_type = "Normal"
            if i == 0:
                room_type = "Spawn"  # Première salle
            elif i == len(rooms) - 1:
                room_type = "Boss"  # Dernière salle
            elif random.random() < 0.2:
                room_type = "Treasure"  # Salle de trésor
            elif random.random() < 0.15:
                room_type = "Trap"  # Salle de piège

            # Attribue le type de salle à toutes ses cellules
            x, y, w, h = room
            for ry in range(y, y + h):
                for rx in range(x, x + w):
                    self.map_data[ry][rx]["room_type"] = room_type

        # Marquez la salle secrète si elle existe
        if self.secret_door:
            door_x, door_y = self.secret_door
            self.map_data[door_y][door_x]["room_type"] = "Secret"

    def add_secret_room(self, rooms):
        """
        Ajoute une salle secrète avec une probabilité de 30%.
        """
        secret_room_probability = random.random()

        if secret_room_probability <= 0.3:
            secret_room_width = 3
            secret_room_height = 3
            secret_room_x = random.randint(1, self.width - secret_room_width - 1)
            secret_room_y = random.randint(1, self.height - secret_room_height - 1)

            self.mark_secret_room((secret_room_x, secret_room_y, secret_room_width, secret_room_height))

            last_room = rooms[-1]
            self.create_corridor(secret_room_x + secret_room_width // 2, secret_room_y + secret_room_height // 2,
                                  last_room[0] + last_room[2] // 2, last_room[1] + last_room[3] // 2)
        else:
            print("Aucune salle secrète générée cette fois.")

    def mark_secret_room(self, room):
        """
        Marque une salle comme secrète et ferme sa porte.
        """
        (rx, ry, rw, rh) = room
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                self.map_data[y][x]["is_secret"] = True
                self.map_data[y][x]["room_type"] = "Secret"  # Marque comme salle secrète

        door_x = rx + rw // 2
        door_y = ry - 1
        if 0 <= door_x < self.width and 0 <= door_y < self.height:
            self.map_data[door_y][door_x]["is_wall"] = True
            self.secret_door = (door_x, door_y)

    def connect_spawn_to_first_room(self, spawn_sas, rooms):
        spawn_x, spawn_y = spawn_sas[0]
        first_room = rooms[0]
        room_x = first_room[0] + first_room[2] // 2
        room_y = first_room[1] + first_room[3] // 2
        self.create_corridor(spawn_x, spawn_y, room_x, room_y)

    def create_corridor(self, start_x, start_y, end_x, end_y):
        if start_x < end_x:
            for x in range(start_x, end_x + 1):
                self.map_data[start_y][x]["is_wall"] = False
        else:
            for x in range(end_x, start_x + 1):
                self.map_data[start_y][x]["is_wall"] = False

        if start_y < end_y:
            for y in range(start_y, end_y + 1):
                self.map_data[y][end_x]["is_wall"] = False
        else:
            for y in range(end_y, start_y + 1):
                self.map_data[y][end_x]["is_wall"] = False

    def init_all_walls(self):
        self.map_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = {
                    "is_wall": True,
                    "has_enemy": False,
                    "has_item": False,
                    "is_secret": False,
                    "room_type": "None"  # Nouveau champ pour le type de salle
                }
                row.append(cell)
            self.map_data.append(row)


    def create_random_rooms(self, num_rooms, min_size, max_size):
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
        (x, y, w, h) = new_room
        for room in rooms:
            (rx, ry, rw, rh) = room
            if (x < rx + rw and x + w > rx and
                y < ry + rh and y + h > ry):
                return True
        return False

    def connect_rooms(self, rooms):
        for i in range(len(rooms) - 1):
            (x1, y1, w1, h1) = rooms[i]
            (x2, y2, w2, h2) = rooms[i + 1]

            cx1 = x1 + w1 // 2
            cy1 = y1 + h1 // 2
            cx2 = x2 + w2 // 2
            cy2 = y2 + h2 // 2

            if cx2 < cx1:
                start_x, end_x = cx2, cx1
            else:
                start_x, end_x = cx1, cx2
            for x in range(start_x, end_x + 1):
                self.map_data[cy1][x]["is_wall"] = False

            if cy2 < cy1:
                start_y, end_y = cy2, cy1
            else:
                start_y, end_y = cy1, cy2
            for y in range(start_y, end_y + 1):
                self.map_data[y][cx2]["is_wall"] = False

    def set_outer_walls(self):
        for x in range(self.width):
            self.map_data[0][x]["is_wall"] = True
            self.map_data[self.height - 1][x]["is_wall"] = True
        for y in range(self.height):
            self.map_data[y][0]["is_wall"] = True
            self.map_data[y][self.width - 1]["is_wall"] = True

    def populate(self, rooms, spawn_sas):
        for (x, y, w, h) in rooms:
            for _ in range(3):
                rx = random.randint(x, x + w - 1)
                ry = random.randint(y, y + h - 1)
                if (rx, ry) in spawn_sas:
                    continue
                if not self.map_data[ry][rx]["is_wall"]:
                    self.map_data[ry][rx]["has_enemy"] = True
                    break

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
