"""Card flip spinner - grid of face-down cards, one flips to reveal winner."""
import random
import time

import pygame

import spinbot.visuals as v


def run_cards(entries, on_winner=None, show_weights=True):
    """Shuffle and eliminate cards to reveal a winner. Returns (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Card Flip")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    winner_name = v.pick_winner(entries)
    color_map = {name: v.COLORS[i % len(v.COLORS)] for i, (name, _) in enumerate(entries)}

    count = len(entries)
    cols = min(5, count)
    rows = (count + cols - 1) // cols

    CARD_W = 130
    CARD_H = 80
    GAP = 12
    grid_w = cols * CARD_W + (cols - 1) * GAP
    grid_h = rows * CARD_H + (rows - 1) * GAP
    grid_x = (v.WIDTH - grid_w) // 2
    grid_y = (v.HEIGHT - grid_h) // 2 - 20

    cards = []
    shuffled = list(entries)
    random.shuffle(shuffled)
    for i, (name, weight) in enumerate(shuffled):
        row = i // cols
        col = i % cols
        x = grid_x + col * (CARD_W + GAP)
        y = grid_y + row * (CARD_H + GAP)
        cards.append({
            "name": name,
            "color": color_map[name],
            "rect": pygame.Rect(x, y, CARD_W, CARD_H),
            "flipped": False,
            "flip_progress": 0.0,
            "is_winner": name == winner_name,
            "eliminated": False,
        })

    CARD_BACK = (v.PANEL_BG[0] + 15, v.PANEL_BG[1] + 15, v.PANEL_BG[2] + 15)
    CARD_BACK_ACCENT = (v.BORDER_COLOR[0] + 10, v.BORDER_COLOR[1] + 10, v.BORDER_COLOR[2] + 10)

    STATE_WAITING = 0
    STATE_SHUFFLING = 1
    STATE_ELIMINATING = 2
    STATE_REVEAL = 3
    STATE_DONE = 4

    state = STATE_WAITING
    phase_start = 0
    shuffle_flip_timer = 0
    eliminate_order = []
    eliminate_idx = 0
    eliminate_timer = 0
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
                    state = STATE_SHUFFLING
                    phase_start = time.time()
                    shuffle_flip_timer = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == STATE_DONE:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        elapsed = time.time() - phase_start if state != STATE_WAITING else 0

        if state == STATE_SHUFFLING:
            shuffle_flip_timer += dt
            if shuffle_flip_timer > 0.08:
                shuffle_flip_timer = 0
                for c in cards:
                    c["flipped"] = random.random() < 0.3
            if elapsed > 2.0:
                for c in cards:
                    c["flipped"] = False
                state = STATE_ELIMINATING
                phase_start = time.time()
                non_winners = [i for i, c in enumerate(cards) if not c["is_winner"]]
                random.shuffle(non_winners)
                eliminate_order = non_winners
                eliminate_idx = 0
                eliminate_timer = 0

        elif state == STATE_ELIMINATING:
            eliminate_timer += dt
            interval = max(0.15, 0.6 - eliminate_idx * 0.04)
            if eliminate_timer > interval and eliminate_idx < len(eliminate_order):
                idx = eliminate_order[eliminate_idx]
                cards[idx]["flipped"] = True
                cards[idx]["eliminated"] = True
                eliminate_idx += 1
                eliminate_timer = 0
            if eliminate_idx >= len(eliminate_order):
                if eliminate_timer > 0.8:
                    state = STATE_REVEAL
                    phase_start = time.time()

        elif state == STATE_REVEAL:
            winner_card = next(c for c in cards if c["is_winner"])
            winner_card["flip_progress"] = min(1.0, elapsed / 0.5)
            if elapsed > 0.5:
                winner_card["flipped"] = True
                if elapsed > 1.0:
                    state = STATE_DONE
                    if on_winner:
                        on_winner(winner_name)

        screen.fill(v.BG_COLOR)

        title = fonts["large"].render("SPINBOT CARDS", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 35)))

        for c in cards:
            rect = c["rect"]

            if c["eliminated"]:
                pygame.draw.rect(screen, v.DARK_BG, rect, border_radius=8)
                pygame.draw.rect(screen, v.BORDER_COLOR, rect, 1, border_radius=8)
                name_text = fonts["small"].render(c["name"], True, v.DIM_TEXT)
                screen.blit(name_text, name_text.get_rect(center=rect.center))
            elif c["is_winner"] and state == STATE_REVEAL:
                p = c["flip_progress"]
                if p < 0.5:
                    scale = 1.0 - p * 2
                    w = max(1, int(CARD_W * scale))
                    shrunk = pygame.Rect(0, 0, w, CARD_H)
                    shrunk.center = rect.center
                    pygame.draw.rect(screen, CARD_BACK, shrunk, border_radius=8)
                else:
                    scale = (p - 0.5) * 2
                    w = max(1, int(CARD_W * scale))
                    grown = pygame.Rect(0, 0, w, CARD_H)
                    grown.center = rect.center
                    pygame.draw.rect(screen, c["color"], grown, border_radius=8)
                    if scale > 0.6:
                        name_text = fonts["medium"].render(c["name"], True, v.TEXT_COLOR)
                        screen.blit(name_text, name_text.get_rect(center=grown.center))
            elif c["flipped"] and state == STATE_SHUFFLING:
                pygame.draw.rect(screen, c["color"], rect, border_radius=8)
                name_text = fonts["small"].render(c["name"], True, v.TEXT_COLOR)
                screen.blit(name_text, name_text.get_rect(center=rect.center))
            elif c["is_winner"] and state == STATE_DONE:
                pygame.draw.rect(screen, c["color"], rect, border_radius=8)
                pygame.draw.rect(screen, v.ACCENT_COLOR, rect, 3, border_radius=8)
                name_text = fonts["medium"].render(c["name"], True, v.TEXT_COLOR)
                screen.blit(name_text, name_text.get_rect(center=rect.center))
            else:
                pygame.draw.rect(screen, CARD_BACK, rect, border_radius=8)
                # Card back pattern
                inner = rect.inflate(-12, -12)
                pygame.draw.rect(screen, CARD_BACK_ACCENT, inner, 2, border_radius=4)
                cx, cy = inner.center
                pygame.draw.line(screen, CARD_BACK_ACCENT, (inner.left + 4, cy), (inner.right - 4, cy), 1)
                pygame.draw.line(screen, CARD_BACK_ACCENT, (cx, inner.top + 4), (cx, inner.bottom - 4), 1)
                pygame.draw.rect(screen, v.BORDER_COLOR, rect, 1, border_radius=8)

        if state == STATE_DONE:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif state == STATE_WAITING:
            v.draw_hint(screen, "Press SPACE to shuffle!", fonts)
        elif state == STATE_ELIMINATING:
            remaining = len(cards) - eliminate_idx
            v.draw_hint(screen, f"Eliminating... {remaining} remaining", fonts)
        elif state == STATE_REVEAL:
            v.draw_hint(screen, "Revealing winner...", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
