"""Bracket/tournament spinner - names face off in rounds until a winner."""
import random
import time

import pygame

import spinbot.visuals as v


def run_bracket(entries, on_winner=None, show_weights=True):
    """Run a single-elimination bracket tournament. Returns (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Bracket")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()

    winner_name = v.pick_winner(entries)
    names = [name for name, _ in entries]
    weights = {name: weight for name, weight in entries}
    color_map = {name: v.COLORS[i % len(v.COLORS)] for i, (name, _) in enumerate(entries)}

    bracket_size = 1
    while bracket_size < len(names):
        bracket_size *= 2
    padded = list(names)
    random.shuffle(padded)
    while len(padded) < bracket_size:
        padded.append(None)

    rounds = [padded]
    current = padded
    while len(current) > 1:
        next_round = []
        for i in range(0, len(current), 2):
            a = current[i]
            b = current[i + 1]
            if a is None:
                next_round.append(b)
            elif b is None:
                next_round.append(a)
            else:
                if a == winner_name:
                    next_round.append(a)
                elif b == winner_name:
                    next_round.append(b)
                else:
                    wa = weights.get(a, 1)
                    wb = weights.get(b, 1)
                    next_round.append(a if random.random() < wa / (wa + wb) else b)
        current = next_round
        rounds.append(current)

    num_rounds = len(rounds)

    STATE_WAITING = 0
    STATE_PLAYING = 1
    STATE_DONE = 2

    state = STATE_WAITING
    visible_round = 0
    reveal_timer = 0
    reveal_interval = 1.0
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
                    state = STATE_PLAYING
                    visible_round = 0
                    reveal_timer = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == STATE_DONE:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        if state == STATE_PLAYING:
            reveal_timer += dt
            if reveal_timer >= reveal_interval:
                reveal_timer = 0
                visible_round += 1
                if visible_round >= num_rounds - 1:
                    state = STATE_DONE
                    if on_winner:
                        on_winner(winner_name)

        screen.fill(v.BG_COLOR)

        title = fonts["large"].render("SPINBOT BRACKET", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 35)))

        margin_x = 30
        margin_top = 75
        usable_w = v.WIDTH - margin_x * 2
        usable_h = v.HEIGHT - margin_top - 100
        col_width = usable_w / num_rounds

        for r_idx, round_entries in enumerate(rounds):
            count = len(round_entries)
            if count == 0:
                continue

            x = margin_x + r_idx * col_width + col_width / 2
            spacing = usable_h / count

            for e_idx, name in enumerate(round_entries):
                y = margin_top + e_idx * spacing + spacing / 2

                revealed = r_idx <= visible_round
                is_current_reveal = r_idx == visible_round and state == STATE_PLAYING

                box_w = min(int(col_width * 0.85), 130)
                box_h = min(int(spacing * 0.7), 36)
                box_rect = pygame.Rect(0, 0, box_w, box_h)
                box_rect.center = (int(x), int(y))

                if name is None:
                    pygame.draw.rect(screen, v.DARK_BG, box_rect, border_radius=4)
                    bye_text = fonts["small"].render("BYE", True, v.DIM_TEXT)
                    screen.blit(bye_text, bye_text.get_rect(center=box_rect.center))
                elif revealed:
                    color = color_map.get(name, v.COLORS[0])
                    lost = False
                    if r_idx + 1 < num_rounds and r_idx + 1 <= visible_round:
                        next_round = rounds[r_idx + 1]
                        match_idx = e_idx // 2
                        if match_idx < len(next_round) and next_round[match_idx] != name:
                            lost = True

                    if lost:
                        pygame.draw.rect(screen, v.DARK_BG, box_rect, border_radius=4)
                        text = fonts["small"].render(name, True, v.DIM_TEXT)
                    else:
                        pygame.draw.rect(screen, color, box_rect, border_radius=4)
                        if is_current_reveal:
                            pygame.draw.rect(screen, v.ACCENT_COLOR, box_rect, 2, border_radius=4)
                        text = fonts["small"].render(name, True, v.TEXT_COLOR)
                    screen.blit(text, text.get_rect(center=box_rect.center))
                else:
                    pygame.draw.rect(screen, v.PANEL_BG, box_rect, border_radius=4)
                    pygame.draw.rect(screen, v.BORDER_COLOR, box_rect, 1, border_radius=4)
                    q = fonts["small"].render("?", True, v.DIM_TEXT)
                    screen.blit(q, q.get_rect(center=box_rect.center))

                if r_idx + 1 < num_rounds and name is not None:
                    next_count = len(rounds[r_idx + 1])
                    next_spacing = usable_h / next_count if next_count else spacing
                    next_y = margin_top + (e_idx // 2) * next_spacing + next_spacing / 2
                    next_x = margin_x + (r_idx + 1) * col_width + col_width / 2
                    pygame.draw.line(screen, v.BORDER_COLOR,
                                     (box_rect.right, int(y)),
                                     (int(next_x) - box_w // 2, int(next_y)), 1)

        if state == STATE_DONE:
            v.draw_winner_banner(screen, winner_name, fonts)
        elif state == STATE_WAITING:
            v.draw_hint(screen, "Press SPACE to start the bracket!", fonts)
        elif state == STATE_PLAYING:
            round_label = f"Round {visible_round + 1} of {num_rounds - 1}"
            v.draw_hint(screen, round_label, fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
