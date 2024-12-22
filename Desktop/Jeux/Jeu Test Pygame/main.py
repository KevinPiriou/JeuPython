# main.py

import pygame
import pygame_gui  # <-- la bibliothèque GUI

import sys

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    MARGIN_X, MARGIN_Y,
    HUD_HEIGHT,
    NUM_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE
)
from dungeon_generator import DungeonGenerator, find_free_tile
from entities import Player, Enemy
from inventory import Inventory, Item

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Roguelike avec HUD Pygame GUI")

    # --- Création du manager pour Pygame GUI ---
    manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Création du panel HUD en haut ---
    hud_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, SCREEN_WIDTH, HUD_HEIGHT),
        manager=manager,
        
    )

    # On ajoute deux labels/textboxes pour HP et Inventaire
    hp_label = pygame_gui.elements.UITextBox(
        html_text="HP : ???",
        relative_rect=pygame.Rect(10, 10, 100, 38),
        manager=manager,
        container=hud_panel
    )
    inv_label = pygame_gui.elements.UITextBox(
        html_text="Inventaire : ???",
        relative_rect=pygame.Rect(120, 10, 150, 38),
        manager=manager,
        container=hud_panel
    )

    # --- Génération du donjon ---
    map_width = 25
    map_height = 18
    dungeon = DungeonGenerator(map_width, map_height)
    map_data = dungeon.generate_map(NUM_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE)

    # --- Calcul offset pour centrer la map ---
    total_map_width_pixels = map_width * TILE_SIZE
    total_map_height_pixels = map_height * TILE_SIZE

    offset_x = (SCREEN_WIDTH - total_map_width_pixels) // 2 - MARGIN_X
    offset_y = (SCREEN_HEIGHT - total_map_height_pixels) // 2 - MARGIN_Y

    # Décalage pour laisser la place au HUD en haut
    offset_y += HUD_HEIGHT

    # --- Création du joueur ---
    spawn_tile = find_free_tile(map_data)
    if spawn_tile:
        spawn_x, spawn_y = spawn_tile
        player_x = spawn_x * TILE_SIZE + offset_x + TILE_SIZE // 2
        player_y = spawn_y * TILE_SIZE + offset_y + TILE_SIZE // 2
        player = Player(player_x, player_y, 100)
    else:
        player = Player(50, 50, 100)

    # Inventaire
    inventory = Inventory()

    # --- Création des ennemis / items ---
    enemies = []
    items_on_floor = []
    for y in range(map_height):
        for x in range(map_width):
            cell = map_data[y][x]
            if cell["has_enemy"]:
                ex = x * TILE_SIZE + offset_x + TILE_SIZE // 2
                ey = y * TILE_SIZE + offset_y + TILE_SIZE // 2
                if not cell["is_wall"]:
                    enemies.append(Enemy(ex, ey, 50))
            if cell["has_item"]:
                ix = x * TILE_SIZE + offset_x + TILE_SIZE // 2
                iy = y * TILE_SIZE + offset_y + TILE_SIZE // 2
                if not cell["is_wall"]:
                    potion = Item("Potion", "heal", 20)
                    items_on_floor.append({"x": ix, "y": iy, "item": potion})

    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0

        # 1) Gestion des events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # On transmet l'event au manager Pygame GUI
            manager.process_events(event)

            # Exemples de touches
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # attaquer le premier ennemi vivant
                    for e in enemies:
                        if e.is_alive():
                            player.attack(e)
                if event.key == pygame.K_1:
                    inventory.use_item(0, player)

        # 2) Mises à jour (déplacement, collisions, etc.)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_DOWN]:
            dy = 1

        old_x, old_y = player.x, player.y
        player.move(dx, dy)

        # Collision mur pour le joueur
        tile_x = int((player.x - offset_x) // TILE_SIZE)
        tile_y = int((player.y - offset_y) // TILE_SIZE)
        if 0 <= tile_x < map_width and 0 <= tile_y < map_height:
            if map_data[tile_y][tile_x]["is_wall"]:
                player.x, player.y = old_x, old_y
        else:
            player.x, player.y = old_x, old_y

        # Update des ennemis
        for e in enemies:
            if e.is_alive():
                e.update(player, map_data, offset_x, offset_y, TILE_SIZE)

        # Ramassage d'objets
        for item_dict in items_on_floor[:]:
            dist = ((player.x - item_dict["x"])**2 + (player.y - item_dict["y"])**2)**0.5
            if dist < 20:
                inventory.add_item(item_dict["item"])
                items_on_floor.remove(item_dict)

        # 3) Mise à jour du manager (GUI)
        manager.update(time_delta)

        # On met à jour les textes du HUD (HP, inventaire)
        hp_label.set_text(f"HP : {player.hp}")
        inv_label.set_text(f"Inventaire : {len(inventory.items)}")

        # 4) Rendu
        screen.fill((0, 0, 0))

        # Dessin du donjon
        for row_idx in range(map_height):
            for col_idx in range(map_width):
                cell = map_data[row_idx][col_idx]
                draw_x = col_idx * TILE_SIZE + offset_x
                draw_y = row_idx * TILE_SIZE + offset_y

                if cell["is_wall"]:
                    color = (40, 40, 40)
                else:
                    color = (100, 100, 100)

                rect = pygame.Rect(draw_x, draw_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)

        # Dessin du joueur
        pygame.draw.circle(screen, (0, 255, 0), (int(player.x), int(player.y)), 10)

        # Dessin des ennemis
        for e in enemies:
            if e.is_alive():
                pygame.draw.circle(screen, (255, 0, 0), (int(e.x), int(e.y)), 8)

        # Dessin des items
        for item_dict in items_on_floor:
            pygame.draw.circle(screen, (0, 0, 255),
                               (int(item_dict["x"]), int(item_dict["y"])), 5)

        # Dessin de l'UI (panel HUD, labels...)
        manager.draw_ui(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
