"""Tarot card pull - cards fan out face down, one is drawn and flipped to reveal."""
import random
import math
import time

import pygame

import spinbot.visuals as v


def run_tarot(entries, on_winner=None, show_weights=True):
    """Fan out tarot cards and draw one to reveal the winner. Returns (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Tarot Pull")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()
    font_title = pygame.font.SysFont("segoeui", 28, bold=True)
    font_card_name = pygame.font.SysFont("segoeui", 20, bold=True)
    font_mystic = pygame.font.SysFont("segoeui", 14)

    winner_name = v.pick_winner(entries)
    color_map = {name: v.COLORS[i % len(v.COLORS)] for i, (name, _) in enumerate(entries)}

    CARD_W = 100
    CARD_H = 160
    count = len(entries)

    # Fan layout - cards spread in an arc
    fan_cx = v.WIDTH // 2
    fan_cy = v.HEIGHT + 200
    fan_radius = 450
    total_arc = min(count * 8, 120)
    start_angle = 90 + total_arc / 2

    shuffled = list(entries)
    random.shuffle(shuffled)
    winner_idx = next(i for i, (n, _) in enumerate(shuffled) if n == winner_name)

    cards = []
    for i, (name, weight) in enumerate(shuffled):
        angle = start_angle - (i / max(1, count - 1)) * total_arc if count > 1 else 90
        rad = math.radians(angle)
        cx = fan_cx + fan_radius * math.cos(rad)
        cy = fan_cy - fan_radius * math.sin(rad)
        cards.append({
            "name": name,
            "color": color_map[name],
            "x": cx,
            "y": cy,
            "angle": angle - 90,
            "is_winner": name == winner_name,
        })

    # Mystical symbols for card backs
    symbols = ["*", "+", "~", "o", "^"]

    STATE_WAITING = 0
    STATE_HOVERING = 1    # Cards glow one by one
    STATE_DRAWING = 2     # Winner card slides up
    STATE_FLIPPING = 3    # Card flips to reveal
    STATE_DONE = 4

    state = STATE_WAITING
    phase_start = 0
    hover_idx = 0
    hover_timer = 0
    draw_progress = 0
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
                elif event.key == pygame.K_SPACE and state == STATE_WAITING:
                    state = STATE_HOVERING
                    phase_start = time.time()
                    hover_idx = 0
                    hover_timer = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == STATE_DONE:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        elapsed = time.time() - phase_start if state != STATE_WAITING else 0

        if state == STATE_HOVERING:
            hover_timer += dt
            speed = max(0.04, 0.2 - elapsed * 0.02)
            if hover_timer >= speed:
                hover_timer = 0
                hover_idx = (hover_idx + 1) % count
            # After cycling for a while, land on winner
            if elapsed > 3.0 and hover_idx == winner_idx:
                state = STATE_DRAWING
                phase_start = time.time()
                draw_progress = 0

        elif state == STATE_DRAWING:
            draw_progress = min(1.0, elapsed / 1.0)
            if draw_progress >= 1.0:
                state = STATE_FLIPPING
                phase_start = time.time()

        elif state == STATE_FLIPPING:
            if elapsed > 1.0:
                state = STATE_DONE
                if on_winner:
                    on_winner(winner_name)

        # Draw
        screen.fill(v.BG_COLOR)

        # Mystical background particles
        t = time.time()
        for i in range(20):
            px = (v.WIDTH * 0.1 + (i * 137.5) % (v.WIDTH * 0.8))
            py = (v.HEIGHT * 0.1 + (i * 97.3 + t * 15) % (v.HEIGHT * 0.7))
            alpha = int(30 + 20 * math.sin(t * 0.5 + i))
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*v.ACCENT_COLOR, alpha), (2, 2), 2)
            screen.blit(s, (int(px), int(py)))

        title = font_title.render("THE FATES DECIDE...", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 35)))

        # Draw cards in fan
        for i, card in enumerate(cards):
            is_hovered = (state == STATE_HOVERING and i == hover_idx)
            is_drawing = card["is_winner"] and state in (STATE_DRAWING, STATE_FLIPPING, STATE_DONE)

            # Card position
            cx, cy = card["x"], card["y"]
            angle = card["angle"]

            if is_drawing:
                # Slide card up to center
                target_x, target_y = v.WIDTH // 2, v.HEIGHT // 2 - 40
                p = draw_progress if state == STATE_DRAWING else 1.0
                ease = 1 - (1 - p) ** 3
                cx = card["x"] + (target_x - card["x"]) * ease
                cy = card["y"] + (target_y - card["y"]) * ease
                angle = card["angle"] * (1 - ease)

            # Create card surface
            card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)

            if is_drawing and state == STATE_FLIPPING:
                flip_p = min(1.0, elapsed / 0.8)
                if flip_p < 0.5:
                    # Back side shrinking
                    _draw_card_back(card_surf, CARD_W, CARD_H, symbols[i % len(symbols)])
                    scale_x = max(0.01, 1.0 - flip_p * 2)
                    scaled = pygame.transform.scale(card_surf, (max(1, int(CARD_W * scale_x)), CARD_H))
                    rect = scaled.get_rect(center=(int(cx), int(cy)))
                    screen.blit(scaled, rect)
                else:
                    # Front side growing
                    _draw_card_front(card_surf, CARD_W, CARD_H, card["name"], card["color"], fonts)
                    scale_x = max(0.01, (flip_p - 0.5) * 2)
                    scaled = pygame.transform.scale(card_surf, (max(1, int(CARD_W * scale_x)), CARD_H))
                    rect = scaled.get_rect(center=(int(cx), int(cy)))
                    screen.blit(scaled, rect)
            elif is_drawing and state == STATE_DONE:
                _draw_card_front(card_surf, CARD_W, CARD_H, card["name"], card["color"], fonts)
                # Glow
                glow = pygame.Surface((CARD_W + 20, CARD_H + 20), pygame.SRCALPHA)
                ar, ag, ab = v.ACCENT_COLOR
                pygame.draw.rect(glow, (ar, ag, ab, 40), glow.get_rect(), border_radius=12)
                screen.blit(glow, (int(cx) - CARD_W // 2 - 10, int(cy) - CARD_H // 2 - 10))
                rect = card_surf.get_rect(center=(int(cx), int(cy)))
                screen.blit(card_surf, rect)
            else:
                _draw_card_back(card_surf, CARD_W, CARD_H, symbols[i % len(symbols)])

                if is_hovered:
                    # Glow effect
                    glow = pygame.Surface((CARD_W + 16, CARD_H + 16), pygame.SRCALPHA)
                    ar, ag, ab = v.ACCENT_COLOR
                    pulse = 0.5 + 0.5 * math.sin(time.time() * 6)
                    pygame.draw.rect(glow, (ar, ag, ab, int(60 * pulse)), glow.get_rect(), border_radius=10)
                    rotated_glow = pygame.transform.rotate(glow, angle)
                    screen.blit(rotated_glow, rotated_glow.get_rect(center=(int(cx), int(cy) - 8)))

                rotated = pygame.transform.rotate(card_surf, angle)
                offset_y = -8 if is_hovered else 0
                rect = rotated.get_rect(center=(int(cx), int(cy) + offset_y))
                screen.blit(rotated, rect)

        if state == STATE_DONE:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif state == STATE_WAITING:
            v.draw_hint(screen, "Press SPACE to draw a card...", fonts)
        elif state == STATE_HOVERING:
            v.draw_hint(screen, "The spirits are choosing...", fonts)
        elif state == STATE_DRAWING:
            v.draw_hint(screen, "A card has been drawn...", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action


def _draw_card_back(surf, w, h, symbol):
    """Draw a mystical card back."""
    # Dark card with border
    pygame.draw.rect(surf, (v.PANEL_BG[0] + 8, v.PANEL_BG[1] + 8, v.PANEL_BG[2] + 12), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(surf, v.BORDER_COLOR, (0, 0, w, h), 2, border_radius=8)

    # Inner frame
    inner = pygame.Rect(8, 8, w - 16, h - 16)
    pygame.draw.rect(surf, v.BORDER_COLOR, inner, 1, border_radius=4)

    # Center symbol
    font = pygame.font.SysFont("segoeui", 28, bold=True)
    sym = font.render(symbol, True, v.DIM_TEXT)
    surf.blit(sym, sym.get_rect(center=(w // 2, h // 2)))

    # Corner dots
    for dx, dy in [(16, 16), (w - 16, 16), (16, h - 16), (w - 16, h - 16)]:
        pygame.draw.circle(surf, v.DIM_TEXT, (dx, dy), 2)


def _draw_card_front(surf, w, h, name, color, fonts):
    """Draw a revealed tarot card face."""
    pygame.draw.rect(surf, color, (0, 0, w, h), border_radius=8)
    pygame.draw.rect(surf, v.ACCENT_COLOR, (0, 0, w, h), 2, border_radius=8)

    # Inner frame
    inner = pygame.Rect(6, 6, w - 12, h - 12)
    pygame.draw.rect(surf, (min(255, color[0] + 20), min(255, color[1] + 20), min(255, color[2] + 20)),
                     inner, 1, border_radius=4)

    # Name centered
    text = fonts["medium"].render(name, True, v.TEXT_COLOR)
    # Scale down if too wide
    if text.get_width() > w - 16:
        text = fonts["small"].render(name, True, v.TEXT_COLOR)
    surf.blit(text, text.get_rect(center=(w // 2, h // 2)))

    # Star at top and bottom
    star_font = pygame.font.SysFont("segoeui", 16)
    star = star_font.render("*", True, v.ACCENT_COLOR)
    surf.blit(star, star.get_rect(center=(w // 2, 18)))
    surf.blit(star, star.get_rect(center=(w // 2, h - 18)))
