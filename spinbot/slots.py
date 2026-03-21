"""Slot machine spinner - three reels lock in one by one."""
import random
import time

import pygame

import spinbot.visuals as v


def run_slots(entries, on_winner=None, show_weights=True):
    """Run a three-reel slot machine and return (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Slots")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    winner_name = v.pick_winner(entries)
    names = [name for name, _ in entries]
    color_map = {name: v.COLORS[i % len(v.COLORS)] for i, (name, _) in enumerate(entries)}

    reels = []
    for _ in range(3):
        reel = names * 3
        random.shuffle(reel)
        reel.append(winner_name)
        reels.append(reel)

    REEL_WIDTH = 200
    REEL_HEIGHT = 400
    REEL_GAP = 30
    CELL_HEIGHT = 50
    total_width = REEL_WIDTH * 3 + REEL_GAP * 2
    start_x = (v.WIDTH - total_width) // 2
    reel_top = 100

    scroll_speeds = [random.uniform(800, 1200) for _ in range(3)]
    stop_times = [2.0 + i * 1.2 + random.random() * 0.5 for i in range(3)]
    reel_offsets = [0.0] * 3
    reel_stopped = [False] * 3
    reel_targets = []
    for reel in reels:
        idx = len(reel) - 1
        reel_targets.append(idx * CELL_HEIGHT)

    spinning = False
    spin_start = 0
    finished = False
    action = "quit"

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not spinning and not finished:
                    spinning = True
                    spin_start = time.time()
                    reel_stopped = [False] * 3
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and finished:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        if spinning:
            elapsed = time.time() - spin_start
            all_stopped = True
            for i in range(3):
                if not reel_stopped[i]:
                    if elapsed < stop_times[i]:
                        reel_offsets[i] += scroll_speeds[i] * dt
                        all_stopped = False
                    else:
                        reel_offsets[i] = reel_targets[i]
                        reel_stopped[i] = True

            if all_stopped:
                spinning = False
                finished = True
                if on_winner:
                    on_winner(winner_name)

        screen.fill(v.BG_COLOR)

        title = fonts["large"].render("SPINBOT SLOTS", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 50)))

        for r in range(3):
            rx = start_x + r * (REEL_WIDTH + REEL_GAP)

            reel_rect = pygame.Rect(rx, reel_top, REEL_WIDTH, REEL_HEIGHT)
            pygame.draw.rect(screen, v.PANEL_BG, reel_rect)
            pygame.draw.rect(screen, v.BORDER_COLOR, reel_rect, 2)

            screen.set_clip(reel_rect)

            reel = reels[r]
            offset = reel_offsets[r]
            center_y = reel_top + REEL_HEIGHT // 2
            base_idx = int(offset // CELL_HEIGHT)
            pixel_offset = offset % CELL_HEIGHT

            visible_cells = REEL_HEIGHT // CELL_HEIGHT + 2
            for j in range(-visible_cells // 2, visible_cells // 2 + 1):
                idx = (base_idx + j) % len(reel)
                name = reel[idx]
                cy = center_y - j * CELL_HEIGHT + pixel_offset - CELL_HEIGHT // 2

                color = color_map.get(name, v.COLORS[0])
                cell_rect = pygame.Rect(rx + 4, cy, REEL_WIDTH - 8, CELL_HEIGHT - 4)
                pygame.draw.rect(screen, color, cell_rect, border_radius=6)

                text = fonts["small"].render(name, True, v.TEXT_COLOR)
                screen.blit(text, text.get_rect(center=cell_rect.center))

            screen.set_clip(None)

            highlight_rect = pygame.Rect(rx - 2, center_y - CELL_HEIGHT // 2, REEL_WIDTH + 4, CELL_HEIGHT)
            pygame.draw.rect(screen, v.ACCENT_COLOR, highlight_rect, 3, border_radius=4)

            if reel_stopped[r]:
                check = fonts["medium"].render("*", True, v.ACCENT_COLOR)
                screen.blit(check, check.get_rect(center=(rx + REEL_WIDTH // 2, reel_top + REEL_HEIGHT + 20)))

        if finished:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif not spinning:
            v.draw_hint(screen, "Press SPACE to pull the lever!", fonts)
        else:
            v.draw_hint(screen, "Spinning...", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
