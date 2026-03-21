"""Name cascade spinner - names rapidly cycle and slow down to land on winner."""
import random
import time

import pygame

import spinbot.visuals as v


def run_cascade(entries, on_winner=None, show_weights=True):
    """Rapidly cycle names and decelerate to a winner. Returns (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Cascade")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    font_big = pygame.font.SysFont("segoeui", 64, bold=True)
    font_history = pygame.font.SysFont("segoeui", 24)

    winner_name = v.pick_winner(entries)
    names = [name for name, _ in entries]
    color_map = {name: v.COLORS[i % len(v.COLORS)] for i, (name, _) in enumerate(entries)}

    sequence = []
    for _ in range(80):
        sequence.append(random.choice(names))
    sequence.append(winner_name)

    spin_duration = 4.0 + random.random() * 1.0
    spinning = False
    spin_start = 0
    current_idx = 0
    finished = False
    action = "quit"

    history = []
    MAX_HISTORY = 8
    last_switch = 0

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
                    current_idx = 0
                    history = []
                    last_switch = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and finished:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        if spinning:
            elapsed = time.time() - spin_start
            progress = min(elapsed / spin_duration, 1.0)

            base_interval = 0.03
            max_interval = 0.5
            interval = base_interval + (max_interval - base_interval) * (progress ** 3)

            last_switch += dt
            if last_switch >= interval and current_idx < len(sequence) - 1:
                last_switch = 0
                current_idx += 1
                history.append(sequence[current_idx])
                if len(history) > MAX_HISTORY:
                    history.pop(0)

            if progress >= 1.0 or current_idx >= len(sequence) - 1:
                current_idx = len(sequence) - 1
                spinning = False
                finished = True
                if on_winner:
                    on_winner(winner_name)

        screen.fill(v.BG_COLOR)

        title = fonts["large"].render("SPINBOT CASCADE", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 50)))

        # Main display box
        box_rect = pygame.Rect(v.WIDTH // 2 - 300, 150, 600, 120)
        pygame.draw.rect(screen, v.PANEL_BG, box_rect, border_radius=12)
        pygame.draw.rect(screen, v.BORDER_COLOR if not finished else v.ACCENT_COLOR,
                         box_rect, 3, border_radius=12)

        if spinning or finished:
            name = sequence[current_idx]
            color = color_map.get(name, v.COLORS[0])

            if spinning:
                pulse = abs(time.time() % 0.2 - 0.1) / 0.1
                r = min(255, color[0] + int(40 * pulse))
                g = min(255, color[1] + int(40 * pulse))
                b = min(255, color[2] + int(40 * pulse))
                color = (r, g, b)

            text = font_big.render(name, True, color)
            screen.blit(text, text.get_rect(center=box_rect.center))
        else:
            text = fonts["large"].render("???", True, v.DIM_TEXT)
            screen.blit(text, text.get_rect(center=box_rect.center))

        # History trail
        if history:
            trail_y = 320
            trail_label = fonts["hint"].render("Recent:", True, v.DIM_TEXT)
            screen.blit(trail_label, (v.WIDTH // 2 - 280, trail_y))

            for i, name in enumerate(history):
                alpha = (i + 1) / len(history)
                color = color_map.get(name, v.COLORS[0])
                faded = (
                    int(color[0] * alpha * 0.6),
                    int(color[1] * alpha * 0.6),
                    int(color[2] * alpha * 0.6),
                )
                y = trail_y + 30 + i * 28
                text = font_history.render(name, True, faded)
                screen.blit(text, (v.WIDTH // 2 - 280, y))

        # Entrants list
        list_x = v.WIDTH // 2 + 100
        list_y = 320
        list_label = fonts["hint"].render("Entrants:", True, v.DIM_TEXT)
        screen.blit(list_label, (list_x, list_y))
        for i, (name, _) in enumerate(entries):
            y = list_y + 25 + i * 24
            if y > v.HEIGHT - 110:
                more = fonts["small"].render(f"  +{len(entries) - i} more...", True, v.DIM_TEXT)
                screen.blit(more, (list_x, y))
                break
            color = color_map[name]
            if finished and name == winner_name:
                color = v.ACCENT_COLOR
            text = fonts["small"].render(f"  {name}", True, color)
            screen.blit(text, (list_x, y))

        if finished:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif not spinning:
            v.draw_hint(screen, "Press SPACE to start!", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
