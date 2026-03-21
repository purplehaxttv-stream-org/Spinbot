"""Shared visual constants and helpers for all spinner types."""
import random

import pygame

THEMES = {
    "dark": {
        "name": "Dark",
        "colors": [
            (140, 50, 70),    # dark rose
            (70, 90, 140),    # steel blue
            (130, 75, 50),    # burnt sienna
            (85, 65, 120),    # muted purple
            (50, 100, 100),   # dark teal
            (140, 100, 45),   # dark gold
            (100, 50, 90),    # plum
            (55, 85, 65),     # forest green
            (120, 65, 65),    # dusty red
            (65, 75, 110),    # slate
            (110, 85, 55),    # bronze
            (80, 55, 100),    # grape
            (60, 90, 85),     # dark cyan
            (130, 70, 80),    # mauve
            (75, 95, 70),     # moss
            (95, 70, 110),    # lavender dark
        ],
        "bg": (12, 12, 16),
        "text": (210, 210, 220),
        "accent": (200, 170, 110),
        "dim": (80, 80, 95),
        "dark_bg": (8, 8, 12),
        "panel": (20, 20, 26),
        "border": (45, 45, 58),
    },
    "midnight": {
        "name": "Midnight Blue",
        "colors": [
            (45, 80, 140),    # royal blue
            (90, 55, 130),    # indigo
            (40, 100, 120),   # deep teal
            (70, 60, 150),    # deep violet
            (55, 90, 110),    # ocean
            (100, 70, 140),   # amethyst
            (35, 75, 100),    # navy teal
            (80, 65, 120),    # dusk purple
            (50, 95, 130),    # cerulean
            (110, 60, 110),   # orchid
            (40, 85, 85),     # dark sea
            (75, 75, 145),    # periwinkle dark
            (60, 100, 100),   # spruce
            (95, 55, 120),    # byzantium
            (45, 70, 120),    # steel
            (85, 80, 135),    # twilight
        ],
        "bg": (8, 10, 20),
        "text": (190, 200, 225),
        "accent": (120, 160, 230),
        "dim": (60, 70, 100),
        "dark_bg": (5, 7, 15),
        "panel": (14, 18, 32),
        "border": (35, 45, 70),
    },
    "ember": {
        "name": "Ember",
        "colors": [
            (160, 50, 40),    # crimson
            (180, 90, 30),    # burnt orange
            (140, 40, 55),    # dark red
            (170, 110, 35),   # amber
            (120, 35, 45),    # maroon
            (155, 75, 30),    # rust
            (130, 55, 40),    # terracotta
            (185, 120, 40),   # dark gold
            (110, 40, 50),    # wine
            (165, 85, 35),    # copper
            (145, 50, 45),    # brick
            (175, 100, 30),   # caramel
            (100, 45, 55),    # burgundy
            (150, 65, 35),    # sienna
            (135, 45, 50),    # garnet
            (160, 95, 35),    # ochre
        ],
        "bg": (16, 10, 8),
        "text": (225, 210, 195),
        "accent": (230, 150, 60),
        "dim": (100, 75, 65),
        "dark_bg": (12, 7, 5),
        "panel": (28, 18, 14),
        "border": (65, 45, 35),
    },
    "void": {
        "name": "Void",
        "colors": [
            (90, 40, 110),    # deep purple
            (50, 50, 80),     # dark slate
            (75, 35, 95),     # nightshade
            (40, 45, 70),     # charcoal blue
            (100, 45, 85),    # dark magenta
            (55, 55, 90),     # storm
            (85, 40, 100),    # eggplant
            (45, 50, 75),     # gunmetal
            (110, 50, 90),    # dark orchid
            (60, 45, 80),     # shadow
            (80, 35, 105),    # imperial
            (50, 55, 85),     # ink
            (95, 45, 95),     # mulberry
            (65, 50, 75),     # onyx
            (70, 40, 90),     # raisin
            (55, 50, 70),     # graphite
        ],
        "bg": (8, 6, 12),
        "text": (185, 180, 200),
        "accent": (160, 120, 200),
        "dim": (70, 65, 85),
        "dark_bg": (5, 3, 8),
        "panel": (16, 12, 22),
        "border": (40, 35, 55),
    },
    "neon": {
        "name": "Neon",
        "colors": [
            (255, 0, 102),    # neon pink
            (0, 180, 255),    # neon blue
            (255, 200, 0),    # neon yellow
            (180, 0, 255),    # neon purple
            (255, 106, 0),    # neon orange
            (0, 220, 220),    # neon cyan
            (255, 0, 200),    # neon magenta
            (0, 136, 255),    # neon cobalt
            (255, 170, 0),    # neon amber
            (200, 0, 255),    # neon violet
            (255, 51, 51),    # neon red
            (0, 200, 180),    # neon aqua
            (255, 136, 255),  # neon rose
            (100, 180, 255),  # neon sky
            (255, 80, 150),   # neon coral
            (150, 0, 220),    # neon grape
        ],
        "bg": (10, 10, 18),
        "text": (240, 240, 255),
        "accent": (0, 230, 200),
        "dim": (100, 100, 130),
        "dark_bg": (5, 5, 12),
        "panel": (18, 18, 30),
        "border": (50, 50, 80),
    },
}

# Active theme - defaults, overridden by set_theme()
_active = THEMES["dark"]
COLORS = _active["colors"]
BG_COLOR = _active["bg"]
TEXT_COLOR = _active["text"]
ACCENT_COLOR = _active["accent"]
DIM_TEXT = _active["dim"]
DARK_BG = _active["dark_bg"]
PANEL_BG = _active["panel"]
BORDER_COLOR = _active["border"]

WIDTH = 800
HEIGHT = 700


def set_theme(theme_key):
    """Switch the active theme. Updates all module-level color vars."""
    global COLORS, BG_COLOR, TEXT_COLOR, ACCENT_COLOR, DIM_TEXT, DARK_BG, PANEL_BG, BORDER_COLOR, _active
    _active = THEMES.get(theme_key, THEMES["dark"])
    COLORS = _active["colors"]
    BG_COLOR = _active["bg"]
    TEXT_COLOR = _active["text"]
    ACCENT_COLOR = _active["accent"]
    DIM_TEXT = _active["dim"]
    DARK_BG = _active["dark_bg"]
    PANEL_BG = _active["panel"]
    BORDER_COLOR = _active["border"]


def get_theme():
    """Return the current active theme dict."""
    return _active


def pick_winner(entries):
    """Weighted random pick from entries list."""
    names, weights = zip(*entries)
    return random.choices(names, weights=weights, k=1)[0]


def get_fonts():
    """Return standard font set."""
    return {
        "small": pygame.font.SysFont("segoeui", 16, bold=True),
        "medium": pygame.font.SysFont("segoeui", 22, bold=True),
        "large": pygame.font.SysFont("segoeui", 36, bold=True),
        "hint": pygame.font.SysFont("segoeui", 18),
    }


def draw_winner_banner(screen, name, fonts):
    """Draw winner text and Back to Menu / Quit buttons at bottom of screen."""
    text = fonts["large"].render(f"WINNER: {name}!", True, ACCENT_COLOR)
    screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT - 80)))

    btn_w, btn_h = 160, 36
    gap = 20
    total_w = btn_w * 2 + gap
    left_x = WIDTH // 2 - total_w // 2
    btn_y = HEIGHT - 42

    menu_rect = pygame.Rect(left_x, btn_y, btn_w, btn_h)
    quit_rect = pygame.Rect(left_x + btn_w + gap, btn_y, btn_w, btn_h)

    mouse_pos = pygame.mouse.get_pos()
    for rect, label in [(menu_rect, "Back to Menu"), (quit_rect, "Quit")]:
        color = PANEL_BG
        if rect.collidepoint(mouse_pos):
            color = (min(255, color[0] + 20), min(255, color[1] + 20), min(255, color[2] + 20))
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1, border_radius=8)
        lbl = fonts["hint"].render(label, True, TEXT_COLOR)
        screen.blit(lbl, lbl.get_rect(center=rect.center))

    return menu_rect, quit_rect


def check_winner_buttons(click_pos):
    """Return button rects for hit testing. Call after draw_winner_banner."""
    btn_w, btn_h = 160, 36
    gap = 20
    total_w = btn_w * 2 + gap
    left_x = WIDTH // 2 - total_w // 2
    btn_y = HEIGHT - 42
    menu_rect = pygame.Rect(left_x, btn_y, btn_w, btn_h)
    quit_rect = pygame.Rect(left_x + btn_w + gap, btn_y, btn_w, btn_h)
    if menu_rect.collidepoint(click_pos):
        return "menu"
    if quit_rect.collidepoint(click_pos):
        return "quit"
    return None


def draw_hint(screen, message, fonts):
    """Draw a hint at the bottom of screen."""
    hint = fonts["hint"].render(message, True, DIM_TEXT)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))


def base_loop(screen, clock, update_fn, draw_fn):
    """
    Common game loop.
    update_fn(events, dt) -> should return False to stop.
    draw_fn(screen) -> draws the frame.
    """
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        if running:
            result = update_fn(events, dt)
            if result is False:
                running = False
            draw_fn(screen)
            pygame.display.flip()
