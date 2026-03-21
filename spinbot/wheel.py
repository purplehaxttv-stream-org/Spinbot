"""Classic spinning wheel."""
import math
import random
import time

import pygame

import spinbot.visuals as v

POINTER_COLOR = (255, 255, 255)


def run_wheel(entries, on_winner=None, show_weights=True):
    """Spin a prize wheel and return (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Wheel")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    WHEEL_CENTER = (v.WIDTH // 2, 330)
    WHEEL_RADIUS = 270

    total_weight = sum(w for _, w in entries)
    equal_fraction = 1.0 / len(entries)
    slices = []
    for i, (name, weight) in enumerate(entries):
        slices.append({
            "name": name,
            "weight": weight,
            "fraction": weight / total_weight if show_weights else equal_fraction,
            "color": v.COLORS[i % len(v.COLORS)],
        })

    winner_name = v.pick_winner(entries)

    angle_offset = 0
    target_angle = 0
    for s in slices:
        arc = s["fraction"] * 360
        if s["name"] == winner_name:
            margin = arc * 0.2
            target_angle = angle_offset + margin + random.random() * (arc - 2 * margin)
            break
        angle_offset += arc

    full_spins = random.randint(5, 8)
    final_rotation = (90 - target_angle) % 360
    total_rotation = full_spins * 360 + final_rotation

    spin_duration = 4.0 + random.random() * 1.5
    spinning = False
    spin_start = 0
    current_rotation = 0
    finished = False
    action = "quit"

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not spinning and not finished:
                    spinning = True
                    spin_start = time.time()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and finished:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        if spinning:
            elapsed = time.time() - spin_start
            progress = min(elapsed / spin_duration, 1.0)
            eased = 1 - (1 - progress) ** 3
            current_rotation = total_rotation * eased
            if progress >= 1.0:
                spinning = False
                finished = True
                current_rotation = total_rotation
                if on_winner:
                    on_winner(winner_name)

        screen.fill(v.BG_COLOR)
        _draw_wheel(screen, WHEEL_CENTER, WHEEL_RADIUS, slices, current_rotation, fonts["small"])

        # Pointer
        px, py = WHEEL_CENTER[0], WHEEL_CENTER[1] - WHEEL_RADIUS - 5
        points = [(px, py - 10), (px - 15, py - 35), (px + 15, py - 35)]
        pygame.draw.polygon(screen, POINTER_COLOR, points)
        pygame.draw.polygon(screen, (0, 0, 0), points, 2)

        # Center
        pygame.draw.circle(screen, v.PANEL_BG, WHEEL_CENTER, 30)
        pygame.draw.circle(screen, POINTER_COLOR, WHEEL_CENTER, 30, 2)

        if finished:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif not spinning:
            v.draw_hint(screen, "Press SPACE to spin!", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action


def _draw_wheel(surface, center, radius, slices, rotation, font):
    cx, cy = center
    start_angle = math.radians(rotation)

    for s in slices:
        arc_rad = s["fraction"] * 2 * math.pi
        end_angle = start_angle + arc_rad

        points = [center]
        steps = max(int(math.degrees(arc_rad) / 2), 3)
        for i in range(steps + 1):
            a = start_angle + arc_rad * i / steps
            x = cx + radius * math.cos(a)
            y = cy - radius * math.sin(a)
            points.append((x, y))
        if len(points) >= 3:
            pygame.draw.polygon(surface, s["color"], points)
            pygame.draw.polygon(surface, v.DARK_BG, points, 1)

        mid_angle = start_angle + arc_rad / 2
        label_dist = radius * 0.65
        lx = cx + label_dist * math.cos(mid_angle)
        ly = cy - label_dist * math.sin(mid_angle)

        text = font.render(s["name"], True, v.TEXT_COLOR)
        angle_deg = -math.degrees(mid_angle)
        rotated = pygame.transform.rotate(text, angle_deg)
        rect = rotated.get_rect(center=(lx, ly))
        surface.blit(rotated, rect)

        start_angle = end_angle
