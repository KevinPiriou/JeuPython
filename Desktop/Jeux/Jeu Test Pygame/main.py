import pygame
import pymunk
import pygame_gui
import sys
import math
import time
from settings import *  # Importation des constantes et couleurs
from dungeon_generator import *
from entities import Player, Enemy
from inventory import Inventory, Item
from projectiles import (
    setup_pymunk_space, add_projectile,
    register_collision_handlers, add_wall,
    PROJECTILE_COLLISION_TYPE, ENEMY_COLLISION_TYPE, WALL_COLLISION_TYPE
)


def main():
    # Initialisation Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Roguelike + Donjon Varié")

    # Initialisation GUI
    manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

    # HUD
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

    # Génération du donjon
    map_width = 35
    map_height = 18
    dungeon = DungeonGenerator(map_width, map_height)
    map_data = dungeon.generate_map(NUM_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE)
    if not map_data:
        print("Erreur : Donjon non généré.")
        return
    print("Donjon généré avec succès.")

    # Calcul des offsets
    total_map_width_pixels = map_width * TILE_SIZE
    total_map_height_pixels = map_height * TILE_SIZE
    offset_x = (SCREEN_WIDTH - total_map_width_pixels) // 2 - MARGIN_X
    offset_y = (SCREEN_HEIGHT - total_map_height_pixels) // 3 - MARGIN_Y
    offset_y += HUD_HEIGHT  # Décalage sous le HUD

    # Initialisation du joueur
    player_tile = (1, 1)
    player_px = player_tile[0] * TILE_SIZE + offset_x + TILE_SIZE // 2
    player_py = player_tile[1] * TILE_SIZE + offset_y + TILE_SIZE // 2
    player = Player(player_px, player_py, 100)
    inventory = Inventory()

    # Initialisation physique
    space = setup_pymunk_space()
    projectiles = []

    # Création des ennemis et murs
    enemies = []
    items_on_floor = []
    for y in range(map_height):
        for x in range(map_width):
            cell = map_data[y][x]
            if cell["has_enemy"]:
                ex = x * TILE_SIZE + offset_x + TILE_SIZE // 2
                ey = y * TILE_SIZE + offset_y + TILE_SIZE // 2
                enemy = Enemy(ex, ey, 50)

                # Ajouter un corps physique pour l'ennemi
                body = pymunk.Body(body_type=pymunk.Body.STATIC)
                body.position = (ex, ey)
                shape = pymunk.Circle(body, 10)
                shape.collision_type = ENEMY_COLLISION_TYPE
                shape.user_data = enemy  # Associer l'ennemi à la forme
                space.add(body, shape)

                enemy.body = body
                enemy.shape = shape
                enemies.append(enemy)

            if cell["has_item"]:
                ix = x * TILE_SIZE + offset_x + TILE_SIZE // 2
                iy = y * TILE_SIZE + offset_y + TILE_SIZE // 2
                items_on_floor.append({"x": ix, "y": iy, "item": Item("Potion", "heal", 20)})

            if cell["is_wall"]:
                wx = x * TILE_SIZE + offset_x
                wy = y * TILE_SIZE + offset_y
                add_wall(space, wx + TILE_SIZE // 2, wy + TILE_SIZE // 2, TILE_SIZE, TILE_SIZE)

    # Enregistrer les gestionnaires de collision
    register_collision_handlers(space, enemies)

    running = True
    while running:
        dt = clock.tick(120) / 1000.0
        fps = clock.get_fps()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
            manager.process_events(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Attaque de mêlée
                    for e in enemies:
                        if e.is_alive():
                            player.attack(e)
                elif event.key == pygame.K_1:
                    inventory.use_item(0, player)

        # Déplacement joueur
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

        # Vérification des collisions avec murs
        tile_x = int((player.x - offset_x) // TILE_SIZE)
        tile_y = int((player.y - offset_y) // TILE_SIZE)
        if 0 <= tile_x < map_width and 0 <= tile_y < map_height:
            if map_data[tile_y][tile_x]["is_wall"]:
                player.x, player.y = old_x, old_y
        else:
            player.x, player.y = old_x, old_y

        # Mise à jour des ennemis
        for e in enemies:
            if e.is_alive():
                e.update(player, map_data, offset_x, offset_y, TILE_SIZE)

        # Ramassage d'items
        for it_dict in items_on_floor[:]:
            dist = math.hypot(player.x - it_dict["x"], player.y - it_dict["y"])
            if dist < 20:
                inventory.add_item(it_dict["item"])
                items_on_floor.remove(it_dict)

        # Gestion des projectiles avec verrouillage
        locked_enemy = None
        min_dist = float('inf')
        for e in enemies:
            if e.is_alive():
                ex, ey = e.body.position  # Utiliser les coordonnées physiques
                dist = math.hypot(player.x - ex, player.y - ey)
                if dist < LOCK_RANGE and dist < min_dist:
                    min_dist = dist
                    locked_enemy = e

        if locked_enemy:
            current_time = pygame.time.get_ticks()
            if current_time - player.last_shot_time > SHOOT_COOLDOWN_MS:
                target_x, target_y = locked_enemy.body.position
                proj = add_projectile(space, player.x, player.y, target_x, target_y)
                projectiles.append(proj)
                player.last_shot_time = current_time

        # Mise à jour de la physique
        space.step(dt)
        for proj in projectiles[:]:
            px, py = proj.body.position

            # Vérifiez si le projectile est hors de l'écran
            if not (offset_x <= px <= offset_x + map_width * TILE_SIZE) or not (offset_y <= py <= offset_y + map_height * TILE_SIZE):
                space.remove(proj.body, proj.shape)
                projectiles.remove(proj)

            # Vérifiez si le projectile a été supprimé par collision
            if proj.body not in space.bodies:
                projectiles.remove(proj)

        # Déverrouillage de la salle secrète
        all_enemies_dead = all(not e.is_alive() for e in enemies)
        all_items_collected = not items_on_floor
        if all_enemies_dead and all_items_collected:
            door_x, door_y = dungeon.secret_door
            map_data[door_y][door_x]["is_wall"] = False
            print(f"Salle secrète déverrouillée à ({door_x}, {door_y}).")

        # Mise à jour GUI
        manager.update(dt)
        hp_label.set_text(f"HP : {player.hp}")
        inv_label.set_text(f"Inventaire : {len(inventory.items)}")

        # Rendu
        screen.fill(BLACK)
        for row_idx in range(map_height):
            for col_idx in range(map_width):
                cell = map_data[row_idx][col_idx]
                draw_x = col_idx * TILE_SIZE + offset_x
                draw_y = row_idx * TILE_SIZE + offset_y
                color = MUR_COLOR if cell["is_wall"] else TILE_COLOR
                rect = pygame.Rect(draw_x, draw_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)

        pygame.draw.circle(screen, PLAYER_COLOR, (int(player.x), int(player.y)), 10)
        for e in enemies:
            if e.is_alive():
                pygame.draw.circle(screen, ENEMY_COLOR, (int(e.body.position.x), int(e.body.position.y)), 8)
        for it_dict in items_on_floor:
            pygame.draw.circle(screen, ITEM_COLOR, (int(it_dict["x"]), int(it_dict["y"])), 5)
        for proj in projectiles:
            px, py = proj.body.position
            pygame.draw.circle(screen, PROJECTILE_COLOR, (int(px), int(py)), 4)

        footer_font = pygame.font.SysFont("Arial", 16)
        footer_text = f"FPS: {fps:.2f} | Ennemies: {len(enemies)} | Items: {len(items_on_floor)} | Pièces: {NUM_ROOMS} | Tuiles: {map_width * map_height}"
        footer_surface = footer_font.render(footer_text, True, WHITE)
        screen.blit(footer_surface, (10, SCREEN_HEIGHT - 30))
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
