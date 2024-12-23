import pygame
import pygame_gui
import sys
import math
import time
from settings import *  # Importer les couleurs définies dans settings.py

from dungeon_generator import *
from entities import Player, Enemy
from inventory import Inventory, Item
from projectiles import (
    setup_pymunk_space, add_projectile,
    register_collision_handlers,
    PROJECTILE_COLLISION_TYPE, ENEMY_COLLISION_TYPE
)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Roguelike + Pymunk + HUD")

    manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Panel HUD
    hud_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, SCREEN_WIDTH, HUD_HEIGHT),
        manager=manager
    )

    hp_label = pygame_gui.elements.UITextBox(
        html_text="HP : ???",
        relative_rect=pygame.Rect(10, 10, 100, 24),
        manager=manager,
        container=hud_panel
    )
    inv_label = pygame_gui.elements.UITextBox(
        html_text="Inventaire : ???",
        relative_rect=pygame.Rect(120, 10, 150, 24),
        manager=manager,
        container=hud_panel
    )

    map_width = 35
    map_height = 18
    dungeon = DungeonGenerator(map_width, map_height)
    map_data = dungeon.generate_map(NUM_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE)
    if map_data is None:
        print("Erreur : Donjon non généré.")
        return
    else:
        print("Donjon généré avec succès.")

    # Calcul offset
    total_map_width_pixels = map_width * TILE_SIZE
    total_map_height_pixels = map_height * TILE_SIZE
    offset_x = (SCREEN_WIDTH - total_map_width_pixels) // 2 - MARGIN_X
    offset_y = (SCREEN_HEIGHT - total_map_height_pixels) // 3 - MARGIN_Y
    offset_y += HUD_HEIGHT  # Décalage sous le HUD

    # Forcer le spawn du joueur dans (1, 1)
    player_tile = (1, 1)
    player_px = player_tile[0] * TILE_SIZE + offset_x + TILE_SIZE // 2
    player_py = player_tile[1] * TILE_SIZE + offset_y + TILE_SIZE // 2
    player = Player(player_px, player_py, 100)

    inventory = Inventory()

    # Création des ennemis et items
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

    # ---- Pymunk ----
    import pymunk
    space = setup_pymunk_space()

    projectiles = []
    last_shot_time = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        # Récupérer les FPS et Tickrate
        fps = clock.get_fps()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            manager.process_events(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Attaquer un ennemi en melee (démo)
                    for e in enemies:
                        if e.is_alive():
                            player.attack(e)
                if event.key == pygame.K_1:
                    inventory.use_item(0, player)

        # ---- Déplacement Joueur ----
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

        tile_x = int((player.x - offset_x) // TILE_SIZE)
        tile_y = int((player.y - offset_y) // TILE_SIZE)
        if 0 <= tile_x < map_width and 0 <= tile_y < map_height:
            if map_data[tile_y][tile_x]["is_wall"]:
                player.x, player.y = old_x, old_y
        else:
            player.x, player.y = old_x, old_y

        # ---- Update Ennemis ----
        for e in enemies:
            if e.is_alive():
                e.update(player, map_data, offset_x, offset_y, TILE_SIZE)

        # ---- Ramassage Items ----
        for it_dict in items_on_floor[:]:
            dist = math.hypot(player.x - it_dict["x"], player.y - it_dict["y"])
            if dist < 20:
                inventory.add_item(it_dict["item"])
                items_on_floor.remove(it_dict)

        # ---- Auto-Lock + Tir Pymunk ----
        locked_enemy = None
        min_dist = float('inf')
        for e in enemies:
            if e.is_alive():
                dist = math.hypot(e.x - player.x, e.y - player.y)
                if dist < LOCK_RANGE and dist < min_dist:
                    min_dist = dist
                    locked_enemy = e

        if locked_enemy is not None:
            current_time = pygame.time.get_ticks()
            if current_time - player.last_shot_time > SHOOT_COOLDOWN_MS:
                _proj = add_projectile(space, player.x, player.y, locked_enemy.x, locked_enemy.y)
                projectiles.append(_proj)
                player.last_shot_time = current_time

        # ---- MàJ Pymunk (projectiles) ----
        space.step(dt)

        for proj in projectiles[:]:
            px, py = proj.body.position
            if px < offset_x or px > (offset_x + map_width * TILE_SIZE) \
               or py < offset_y or py > (offset_y + map_height * TILE_SIZE):
                space.remove(proj.body, proj.shape)
                projectiles.remove(proj)
                continue

            for e in enemies:
                if e.is_alive():
                    dist = math.hypot(e.x - px, e.y - py)
                    if dist < 10:
                        e.hp -= 20
                        space.remove(proj.body, proj.shape)
                        projectiles.remove(proj)
                        break

        # Vérification si tous les ennemis sont morts pour ouvrir la porte secrète
        all_enemies_dead = all(not e.is_alive() for e in enemies)
        all_items_collected = (len(items_on_floor) == 0)

        if all_enemies_dead and all_items_collected:
            (door_x, door_y) = dungeon.secret_door
            dungeon.map_data[door_y][door_x]["is_wall"] = False
            dungeon.map_data[door_y][door_x]["is_door"] = False
            print(f"Portes de la salle secrète déverrouillées en ({door_x}, {door_y}).")

        # ---- MàJ GUI ----
        manager.update(dt)

        hp_label.set_text(f"HP : {player.hp}")
        inv_label.set_text(f"Inventaire : {len(inventory.items)}")

        # ---- Rendu ----
        screen.fill(BLACK)  # Réinitialisation de l'écran

        # Dessin du donjon
        for row_idx in range(map_height):
            for col_idx in range(map_width):
                cell = map_data[row_idx][col_idx]
                draw_x = col_idx * TILE_SIZE + offset_x
                draw_y = row_idx * TILE_SIZE + offset_y

                color = MUR_COLOR if cell["is_wall"] else TILE_COLOR  # Utilisation des couleurs définies dans settings.py
                rect = pygame.Rect(draw_x, draw_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)

        # Dessin du joueur
        pygame.draw.circle(screen, PLAYER_COLOR, (int(player.x), int(player.y)), 10)

        # Dessin des ennemis
        for e in enemies:
            if e.is_alive():
                pygame.draw.circle(screen, ENEMY_COLOR, (int(e.x), int(e.y)), 8)

        # Dessin des items
        for it_dict in items_on_floor:
            pygame.draw.circle(screen, ITEM_COLOR, (int(it_dict["x"]), int(it_dict["y"])), 5)

        # Dessin des projectiles
        for proj in projectiles:
            px, py = proj.body.position
            pygame.draw.circle(screen, PROJECTILE_COLOR, (int(px), int(py)), 4)

        # Affichage du footer avec les informations
        footer_font = pygame.font.SysFont("Arial", 16)
        footer_text = f"FPS: {fps:.2f} | Ennemies: {len(enemies)} | Items: {len(items_on_floor)} | Pièces: {NUM_ROOMS} | Tuiles: {map_width * map_height}"
        footer_surface = footer_font.render(footer_text, True, WHITE)
        screen.blit(footer_surface, (10, SCREEN_HEIGHT - 30))  # Position du footer

        # HUD
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
