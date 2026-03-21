"""Roulette spinner - ball bounces around a track and lands on a name."""
import math
import random
import time

import pygame

import spinbot.visuals as v


def run_roulette(entries, on_winner=None, show_weights=True):
    """Spin a roulette ball around a track and return (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Roulette")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    CENTER = (v.WIDTH // 2, 320)
    OUTER_R = 260
    INNER_R = 170
    BALL_R = 14

    winner_name = v.pick_winner(entries)

    total_weight = sum(w for _, w in entries)
    equal_frac = 1.0 / len(entries)
    slots = []
    for i, (name, weight) in enumerate(entries):
        slots.append({
            "name": name,
            "fraction": weight / total_weight if show_weights else equal_frac,
            "color": v.COLORS[i % len(v.COLORS)],
        })

    angle_offset = 0
    winner_center_angle = 0
    for s in slots:
        arc = s["fraction"] * 360
        if s["name"] == winner_name:
            winner_center_angle = angle_offset + arc / 2
            break
        angle_offset += arc

    spin_duration = 4.5 + random.random() * 1.5
    total_ball_rotations = random.randint(6, 10) * 360
    final_ball_angle = winner_center_angle

    spinning = False
    spin_start = 0
    ball_angle = 0
    ball_radius = OUTER_R - 25
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and finished:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        if spinning:
            elapsed = time.time() - spin_start
            progress = min(elapsed / spin_duration, 1.0)
            eased = 1 - (1 - progress) ** 4
            ball_angle = final_ball_angle + total_ball_rotations * (1 - eased)
            ball_radius = OUTER_R - 25 - (OUTER_R - INNER_R - 40) * eased

            if progress >= 1.0:
                spinning = False
                finished = True
                ball_angle = final_ball_angle
                if on_winner:
                    on_winner(winner_name)

        screen.fill(v.BG_COLOR)

        title = fonts["large"].render("SPINBOT ROULETTE", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 35)))

        cx, cy = CENTER

        # Outer ring
        pygame.draw.circle(screen, v.PANEL_BG, CENTER, OUTER_R)
        pygame.draw.circle(screen, v.ACCENT_COLOR, CENTER, OUTER_R, 2)

        # Slots
        start_a = 0
        for s in slots:
            arc = s["fraction"] * 2 * math.pi
            end_a = start_a + arc

            points = []
            steps = max(int(math.degrees(arc) / 2), 3)
            for i in range(steps + 1):
                a = start_a + arc * i / steps
                points.append((cx + OUTER_R * math.cos(a), cy - OUTER_R * math.sin(a)))
            for i in range(steps, -1, -1):
                a = start_a + arc * i / steps
                points.append((cx + INNER_R * math.cos(a), cy - INNER_R * math.sin(a)))

            if len(points) >= 3:
                pygame.draw.polygon(screen, s["color"], points)
                pygame.draw.polygon(screen, v.DARK_BG, points, 1)

            mid_a = start_a + arc / 2
            label_r = (OUTER_R + INNER_R) / 2
            lx = cx + label_r * math.cos(mid_a)
            ly = cy - label_r * math.sin(mid_a)
            text = fonts["small"].render(s["name"], True, v.TEXT_COLOR)
            angle_deg = -math.degrees(mid_a)
            rotated = pygame.transform.rotate(text, angle_deg)
            screen.blit(rotated, rotated.get_rect(center=(lx, ly)))

            start_a = end_a

        # Inner circle
        pygame.draw.circle(screen, v.DARK_BG, CENTER, INNER_R)
        pygame.draw.circle(screen, v.ACCENT_COLOR, CENTER, INNER_R, 2)

        # Center
        pygame.draw.circle(screen, v.PANEL_BG, CENTER, 40)
        pygame.draw.circle(screen, v.ACCENT_COLOR, CENTER, 40, 2)
        sp_text = fonts["medium"].render("SB", True, v.ACCENT_COLOR)
        screen.blit(sp_text, sp_text.get_rect(center=CENTER))

        # Ball with glow
        ba_rad = math.radians(ball_angle)
        bx = cx + ball_radius * math.cos(ba_rad)
        by = cy - ball_radius * math.sin(ba_rad)
        ball_pos = (int(bx), int(by))
        glow_surface = pygame.Surface((BALL_R * 8, BALL_R * 8), pygame.SRCALPHA)
        glow_center = (BALL_R * 4, BALL_R * 4)
        ar, ag, ab = v.ACCENT_COLOR
        for r, alpha in [(BALL_R * 3, 25), (BALL_R * 2, 50), (int(BALL_R * 1.5), 80)]:
            pygame.draw.circle(glow_surface, (ar, ag, ab, alpha), glow_center, r)
        screen.blit(glow_surface, (ball_pos[0] - BALL_R * 4, ball_pos[1] - BALL_R * 4))
        ball_bright = (min(255, ar + 50), min(255, ag + 50), min(255, ab + 50))
        pygame.draw.circle(screen, ball_bright, ball_pos, BALL_R)
        pygame.draw.circle(screen, (255, 255, 255), (ball_pos[0] - 4, ball_pos[1] - 4), 5)

        if finished:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif not spinning:
            v.draw_hint(screen, "Press SPACE to spin!", fonts)
        else:
            v.draw_hint(screen, "Spinning...", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
