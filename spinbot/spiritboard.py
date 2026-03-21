"""Spirit board (Ouija) - planchette slides to letters spelling out the winner."""
import random
import math
import time
import string

import pygame

import spinbot.visuals as v

# Board layout constants
ALPHABET = list(string.ascii_uppercase)
NUMBERS = list("1234567890")


def _build_board_layout(board_rect):
    """Build positions for all letters, numbers, YES/NO/GOODBYE on the board."""
    inner = board_rect.inflate(-40, -40)
    positions = {}

    # YES / NO at top
    positions["YES"] = (inner.left + 60, inner.top + 30)
    positions["NO"] = (inner.right - 60, inner.top + 30)

    # Two rows of letters
    row1 = ALPHABET[:13]  # A-M
    row2 = ALPHABET[13:]  # N-Z

    row1_y = inner.top + 90
    row2_y = inner.top + 145
    num_y = inner.top + 200

    for i, ch in enumerate(row1):
        x = inner.left + 20 + (i / 12) * (inner.width - 40)
        positions[ch] = (x, row1_y)

    for i, ch in enumerate(row2):
        x = inner.left + 35 + (i / 12) * (inner.width - 70)
        positions[ch] = (x, row2_y)

    for i, ch in enumerate(NUMBERS):
        x = inner.left + 30 + (i / 9) * (inner.width - 60)
        positions[ch] = (x, num_y)

    # GOODBYE at bottom
    positions["GOODBYE"] = (inner.centerx, inner.bottom - 20)

    return positions


def run_spiritboard(entries, on_winner=None, show_weights=True):
    """Spell out the winner via a moving planchette. Returns (winner_name, action)."""
    if not entries:
        return None

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot - Spirit Board")
    clock = pygame.time.Clock()
    fonts = v.get_fonts()
    font_board = pygame.font.SysFont("segoeui", 22, bold=True)
    font_board_sm = pygame.font.SysFont("segoeui", 16, bold=True)
    font_spelled = pygame.font.SysFont("segoeui", 52, bold=True)
    font_label = pygame.font.SysFont("segoeui", 20, bold=True)

    winner_name = v.pick_winner(entries)

    BOARD_RECT = pygame.Rect(40, 70, v.WIDTH - 80, 280)
    layout = _build_board_layout(BOARD_RECT)

    # Build the letter sequence to spell the winner's name
    letters_to_spell = list(winner_name.upper())

    # Full sequence: short intro wander, then spell with detours between letters
    move_sequence = []

    # 1-2 quick wanders to start
    for _ in range(random.randint(1, 2)):
        move_sequence.append({"char": random.choice(ALPHABET), "pause": 0.15, "is_spelling": False})

    for i, ch in enumerate(letters_to_spell):
        key = ch.upper()
        if key not in layout:
            continue
        # 1-2 detours between letters (not before the first)
        if i > 0:
            detours = random.randint(1, 2)
            for _ in range(detours):
                fake = random.choice(ALPHABET)
                move_sequence.append({"char": fake, "pause": 0.15, "is_spelling": False})
        # Pause on the real letter
        pause = 0.7 if i < len(letters_to_spell) - 1 else 1.0
        move_sequence.append({"char": key, "pause": pause, "is_spelling": True})

    # Planchette state
    start_pos = (float(BOARD_RECT.centerx), float(BOARD_RECT.centery))
    planchette_x, planchette_y = start_pos
    target_x, target_y = start_pos

    STATE_WAITING = 0
    STATE_SPELLING = 1
    STATE_DONE = 2

    state = STATE_WAITING
    move_idx = 0
    move_timer = 0
    arrived = False
    spelled_so_far = ""
    planchette_glow = 0
    letter_flash = 0  # flash timer when a letter locks in
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
                    state = STATE_SPELLING
                    move_idx = 0
                    arrived = False
                    move_timer = 0
                    spelled_so_far = ""
                    if move_sequence:
                        ch = move_sequence[0]["char"]
                        if ch in layout:
                            target_x, target_y = layout[ch]
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == STATE_DONE:
                result = v.check_winner_buttons(event.pos)
                if result:
                    action = result
                    running = False

        # Smooth planchette movement
        speed = 4.0
        planchette_x += (target_x - planchette_x) * speed * dt
        planchette_y += (target_y - planchette_y) * speed * dt

        if state == STATE_SPELLING and move_idx < len(move_sequence):
            dist = math.hypot(planchette_x - target_x, planchette_y - target_y)
            if dist < 5:
                if not arrived:
                    arrived = True
                    move_timer = 0
                move_timer += dt
                current_move = move_sequence[move_idx]
                if move_timer >= current_move["pause"]:
                    # Lock in letter if it's a spelling move
                    if current_move["is_spelling"]:
                        spelled_so_far += current_move["char"]
                        letter_flash = 0.4

                    move_idx += 1
                    arrived = False
                    move_timer = 0
                    if move_idx < len(move_sequence):
                        ch = move_sequence[move_idx]["char"]
                        if ch in layout:
                            target_x, target_y = layout[ch]
                    else:
                        state = STATE_DONE
                        if on_winner:
                            on_winner(winner_name)

        planchette_glow = 0.5 + 0.5 * math.sin(time.time() * 3)
        letter_flash = max(0, letter_flash - dt)

        # Draw
        flicker = random.randint(-2, 2) if state == STATE_SPELLING else 0
        bg = tuple(max(0, c + flicker) for c in v.BG_COLOR)
        screen.fill(bg)

        # Board background
        pygame.draw.rect(screen, v.PANEL_BG, BOARD_RECT, border_radius=16)
        pygame.draw.rect(screen, v.BORDER_COLOR, BOARD_RECT, 2, border_radius=16)
        inner_border = BOARD_RECT.inflate(-16, -16)
        pygame.draw.rect(screen, v.BORDER_COLOR, inner_border, 1, border_radius=12)

        # Title
        title = fonts["large"].render("SPIRIT BOARD", True, v.ACCENT_COLOR)
        screen.blit(title, title.get_rect(center=(v.WIDTH // 2, BOARD_RECT.top - 25)))

        # Draw all board elements
        for key, (kx, ky) in layout.items():
            if key in ("YES", "NO", "GOODBYE"):
                text = font_label.render(key, True, v.ACCENT_COLOR)
            elif len(key) == 1:
                # Check if planchette is hovering this letter
                dist = math.hypot(planchette_x - kx, planchette_y - ky)
                if dist < 25 and state in (STATE_SPELLING, STATE_DONE):
                    # Glow
                    glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
                    ar, ag, ab = v.ACCENT_COLOR
                    pygame.draw.circle(glow_s, (ar, ag, ab, int(80 * planchette_glow)), (20, 20), 20)
                    screen.blit(glow_s, (int(kx) - 20, int(ky) - 20))
                    text = font_board.render(key, True, v.ACCENT_COLOR)
                else:
                    text = font_board.render(key, True, v.TEXT_COLOR)
            else:
                text = font_board_sm.render(key, True, v.DIM_TEXT)
            screen.blit(text, text.get_rect(center=(int(kx), int(ky))))

        # Corner decorations
        corner_font = pygame.font.SysFont("segoeui", 18)
        for pos in [(BOARD_RECT.left + 22, BOARD_RECT.top + 22),
                     (BOARD_RECT.right - 22, BOARD_RECT.top + 22),
                     (BOARD_RECT.left + 22, BOARD_RECT.bottom - 22),
                     (BOARD_RECT.right - 22, BOARD_RECT.bottom - 22)]:
            sym = corner_font.render("*", True, v.DIM_TEXT)
            screen.blit(sym, sym.get_rect(center=pos))

        # Planchette
        px, py = int(planchette_x), int(planchette_y)
        pw, ph = 50, 60

        if state != STATE_WAITING:
            glow_surf = pygame.Surface((pw + 30, ph + 30), pygame.SRCALPHA)
            ar, ag, ab = v.ACCENT_COLOR
            pygame.draw.ellipse(glow_surf, (ar, ag, ab, int(30 * planchette_glow)), glow_surf.get_rect())
            screen.blit(glow_surf, glow_surf.get_rect(center=(px, py)))

        points = [
            (px, py - ph // 2),
            (px - pw // 2, py + 8),
            (px, py + ph // 2),
            (px + pw // 2, py + 8),
        ]
        body_color = (v.PANEL_BG[0] + 25, v.PANEL_BG[1] + 25, v.PANEL_BG[2] + 30)
        pygame.draw.polygon(screen, body_color, points)
        pygame.draw.polygon(screen, v.ACCENT_COLOR, points, 2)

        # Window - transparent hole that shows the letter underneath
        window_center = (px, py - 5)
        window_r = 14
        pygame.draw.circle(screen, v.BG_COLOR, window_center, window_r)
        pygame.draw.circle(screen, v.ACCENT_COLOR, window_center, window_r, 1)

        # Draw the closest letter INSIDE the window so it's visible through the hole
        if state != STATE_WAITING:
            closest_ch = None
            closest_dist = 999
            for key, (kx, ky) in layout.items():
                if len(key) != 1:
                    continue
                d = math.hypot(planchette_x - kx, planchette_y - ky)
                if d < closest_dist:
                    closest_dist = d
                    closest_ch = key
            if closest_ch and closest_dist < 35:
                window_letter = font_board.render(closest_ch, True, v.ACCENT_COLOR)
                screen.blit(window_letter, window_letter.get_rect(center=window_center))

        # Spelled name display area
        spell_area_y = BOARD_RECT.bottom + 30
        pygame.draw.line(screen, v.BORDER_COLOR, (100, spell_area_y + 50), (v.WIDTH - 100, spell_area_y + 50), 1)

        if spelled_so_far:
            # Flash effect on new letter
            color = v.ACCENT_COLOR
            if letter_flash > 0:
                boost = int(80 * (letter_flash / 0.4))
                color = (min(255, color[0] + boost), min(255, color[1] + boost), min(255, color[2] + boost))

            spelled_text = font_spelled.render(spelled_so_far, True, color)
            screen.blit(spelled_text, spelled_text.get_rect(center=(v.WIDTH // 2, spell_area_y + 25)))

            # Underscore placeholders for remaining letters
            remaining = len(winner_name.upper()) - len(spelled_so_far)
            if remaining > 0 and state == STATE_SPELLING:
                # Figure out remaining letters to show as underscores
                full_upper = winner_name.upper()
                remaining_only = [c for c in full_upper if c in layout]
                shown = len(spelled_so_far)
                placeholder = spelled_so_far + " _" * (len(remaining_only) - shown)
                # Just show underscores portion
                underscore_text = font_spelled.render("_" * (len(remaining_only) - shown), True, v.DIM_TEXT)
                ux = v.WIDTH // 2 + spelled_text.get_width() // 2 + 10
                screen.blit(underscore_text, underscore_text.get_rect(midleft=(ux, spell_area_y + 25)))

        if state == STATE_DONE:
            # Winner banner with menu/quit buttons
            v.draw_winner_banner(screen, winner_name, fonts)
        elif state == STATE_WAITING:
            v.draw_hint(screen, "Press SPACE to commune with the spirits...", fonts)
        elif state == STATE_SPELLING:
            v.draw_hint(screen, "The spirits are speaking...", fonts)

        pygame.display.flip()

    pygame.display.quit()
    return winner_name, action
