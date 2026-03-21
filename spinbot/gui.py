"""Main GUI application - all menus and navigation in pygame."""
import importlib

import pygame

import spinbot.visuals as v
from spinbot.firebot import FirebotAPI
from spinbot.config import load_config, save_config

SPINNERS = [
    ("wheel", "Wheel", "spinbot.wheel", "run_wheel"),
    ("slots", "Slot Machine", "spinbot.slots", "run_slots"),
    ("cards", "Card Flip", "spinbot.cards", "run_cards"),
    ("roulette", "Roulette", "spinbot.roulette", "run_roulette"),
    ("bracket", "Bracket", "spinbot.bracket", "run_bracket"),
    ("cascade", "Name Cascade", "spinbot.cascade", "run_cascade"),
    ("tarot", "Tarot Pull", "spinbot.tarot", "run_tarot"),
    ("spiritboard", "Spirit Board", "spinbot.spiritboard", "run_spiritboard"),
]

ODDS_MODES = [
    ("Weighted (visible)", True, True),
    ("Weighted (hidden)", False, True),
    ("Equal (pure random)", False, False),
]


class Button:
    """Clickable, hoverable rectangle with a text label."""

    def __init__(self, rect, text, font, color=None, text_color=None, tag=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color or v.PANEL_BG
        self.text_color = text_color or v.TEXT_COLOR
        self.tag = tag
        self.hovered = False

    def draw(self, screen):
        """Render the button with hover highlight."""
        color = self.color
        if self.hovered:
            color = (min(255, color[0] + 20), min(255, color[1] + 20), min(255, color[2] + 20))
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, v.BORDER_COLOR, self.rect, 1, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def check_click(self, pos):
        """Return True if pos is inside the button rect."""
        return self.rect.collidepoint(pos)


def _build_entries_currency(api, config):
    top_users = api.get_currency_top(config["checkin_currency_name"])
    checkin_id = config["checkin_currency_id"]
    bonus_id = config.get("bonus_currency_id")
    bonus_weight = config.get("bonus_weight", 0)
    entries = []
    for user in top_users:
        name = user["displayName"]
        checkins = user["currency"].get(checkin_id, 0)
        bonus = 0
        if bonus_id:
            bonus = user["currency"].get(bonus_id, 0) * bonus_weight
        total = checkins + bonus
        if total > 0:
            entries.append((name, total))
    return entries


def _build_entries_metadata(api, config):
    checkin_key = config["checkin_metadata_key"]
    bonus_key = config.get("bonus_metadata_key")
    bonus_weight = config.get("bonus_weight", 0)
    viewers = api.get_viewers()
    entries = []
    for viewer in viewers:
        user_id = viewer["id"]
        name = viewer["displayName"]
        try:
            checkins = int(api.get_viewer_metadata(user_id, checkin_key))
        except Exception:
            continue
        bonus = 0
        if bonus_key:
            try:
                bonus = int(api.get_viewer_metadata(user_id, bonus_key)) * bonus_weight
            except Exception:
                pass
        total = checkins + bonus
        if total > 0:
            entries.append((name, total))
    return entries


def build_entries(api, config):
    """Fetch viewer data and return a list of (name, weight) entry tuples."""
    mode = config.get("mode", "currency")
    if mode == "metadata":
        return _build_entries_metadata(api, config)
    return _build_entries_currency(api, config)


def run_app():
    """Launch the main Spinbot GUI loop."""
    api = FirebotAPI()
    config = load_config()

    if config:
        if config.get("custom_theme"):
            v.THEMES["custom"] = config["custom_theme"]
        if config.get("theme"):
            v.set_theme(config["theme"])

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot")
    clock = pygame.time.Clock()

    state = "main"  # main, config_mode, config_currency, config_bonus, config_bonus_weight,
                     # config_meta_key, config_meta_bonus, config_meta_bonus_weight,
                     # spinner_select, odds_select, theme_select
    selected_spinner = None
    status_message = ""
    status_timer = 0

    # For config flow
    config_temp = {}
    currencies_cache = None
    input_text = ""
    input_label = ""
    input_callback = None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        status_timer = max(0, status_timer - dt)

        events = pygame.event.get()
        clicked = None
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = event.pos
            elif event.type == pygame.KEYDOWN and state == "text_input":
                if event.key == pygame.K_RETURN:
                    if input_callback:
                        input_callback(input_text)
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    state = "main"
                else:
                    if event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        screen.fill(v.BG_COLOR)
        fonts = v.get_fonts()

        if state == "main":
            _draw_main_menu(screen, fonts, config, mouse_pos, clicked,
                            lambda s: _set_state_holder(locals(), s),
                            api, status_message if status_timer > 0 else "")

            # Handle button clicks inline since closures are tricky
            buttons = _get_main_buttons(fonts, config)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "configure":
                        state = "config_mode"
                        try:
                            currencies_cache = api.get_currencies()
                        except Exception:
                            currencies_cache = {}
                    elif btn.tag == "theme":
                        state = "theme_select"
                    elif btn.tag == "quit":
                        running = False
                    elif btn.tag and btn.tag.startswith("spinner_"):
                        idx = int(btn.tag.split("_")[1])
                        if config and config.get("mode"):
                            selected_spinner = idx
                            state = "odds_select"
                        else:
                            status_message = "Configure currencies first!"
                            status_timer = 2.0

        elif state == "config_mode":
            _draw_config_mode(screen, fonts, mouse_pos, clicked, config_temp,
                              lambda s: _apply_state(locals(), s))
            buttons = _get_config_mode_buttons(fonts)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "currency":
                        config_temp = {"mode": "currency"}
                        state = "config_currency"
                    elif btn.tag == "metadata":
                        config_temp = {"mode": "metadata"}
                        state = "config_meta_key"
                        input_text = ""
                        input_label = "Enter metadata key for check-ins:"
                    elif btn.tag == "back":
                        state = "main"

        elif state == "config_currency":
            buttons = _get_currency_buttons(fonts, currencies_cache)
            _draw_page_title(screen, fonts, "Select Check-in Currency")
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "back":
                        state = "config_mode"
                    elif btn.tag:
                        cid, cname = btn.tag.split("|", 1)
                        config_temp["checkin_currency_id"] = cid
                        config_temp["checkin_currency_name"] = cname
                        state = "config_bonus"

        elif state == "config_bonus":
            _draw_page_title(screen, fonts, "Bonus Currency (optional)")
            buttons = _get_bonus_buttons(fonts, currencies_cache, config_temp.get("checkin_currency_id"))
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "skip":
                        config_temp["bonus_currency_id"] = None
                        config_temp["bonus_currency_name"] = None
                        config_temp["bonus_weight"] = 0
                        _save_and_apply_config(config_temp, config)
                        config = config_temp
                        save_config(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif btn.tag == "back":
                        state = "config_currency"
                    elif btn.tag:
                        cid, cname = btn.tag.split("|", 1)
                        config_temp["bonus_currency_id"] = cid
                        config_temp["bonus_currency_name"] = cname
                        state = "config_bonus_weight"
                        input_text = "1"
                        input_label = "Extra entries per first check-in:"

        elif state == "config_bonus_weight":
            _draw_text_input(screen, fonts, input_label, input_text)
            if clicked:
                # Check for confirm button
                confirm_rect = pygame.Rect(v.WIDTH // 2 - 60, 400, 120, 40)
                if confirm_rect.collidepoint(clicked):
                    try:
                        config_temp["bonus_weight"] = int(input_text) if input_text else 1
                    except ValueError:
                        config_temp["bonus_weight"] = 1
                    _save_and_apply_config(config_temp, config)
                    config = config_temp
                    save_config(config)
                    state = "main"
                    status_message = "Configuration saved!"
                    status_timer = 2.0
            # Draw confirm button
            confirm_btn = Button((v.WIDTH // 2 - 60, 400, 120, 40), "Confirm", fonts["medium"],
                                 color=v.ACCENT_COLOR, text_color=v.BG_COLOR)
            confirm_btn.check_hover(mouse_pos)
            confirm_btn.draw(screen)
            # Handle typing
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            config_temp["bonus_weight"] = int(input_text) if input_text else 1
                        except ValueError:
                            config_temp["bonus_weight"] = 1
                        _save_and_apply_config(config_temp, config)
                        config = config_temp
                        save_config(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and event.unicode.isdigit() and len(input_text) < 5:
                        input_text += event.unicode

        elif state == "config_meta_key":
            _draw_text_input(screen, fonts, input_label, input_text)
            confirm_btn = Button((v.WIDTH // 2 - 60, 400, 120, 40), "Confirm", fonts["medium"],
                                 color=v.ACCENT_COLOR, text_color=v.BG_COLOR)
            confirm_btn.check_hover(mouse_pos)
            confirm_btn.draw(screen)
            back_btn = Button((v.WIDTH // 2 - 60, 460, 120, 40), "Back", fonts["medium"])
            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)
            if clicked:
                if confirm_btn.check_click(clicked) and input_text:
                    config_temp["checkin_metadata_key"] = input_text
                    config_temp["bonus_metadata_key"] = None
                    config_temp["bonus_weight"] = 0
                    _save_and_apply_config(config_temp, config)
                    config = config_temp
                    save_config(config)
                    state = "main"
                    status_message = "Configuration saved!"
                    status_timer = 2.0
                elif back_btn.check_click(clicked):
                    state = "config_mode"
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text:
                        config_temp["checkin_metadata_key"] = input_text
                        config_temp["bonus_metadata_key"] = None
                        config_temp["bonus_weight"] = 0
                        _save_and_apply_config(config_temp, config)
                        config = config_temp
                        save_config(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        elif state == "odds_select":
            _draw_page_title(screen, fonts, f"Odds Mode - {SPINNERS[selected_spinner][1]}")
            buttons = _get_odds_buttons(fonts)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "back":
                        state = "main"
                    elif btn.tag is not None:
                        idx = int(btn.tag)
                        _, show_w, use_w = ODDS_MODES[idx]
                        # Run the spinner
                        pygame.display.quit()
                        spinner_action = _run_spinner(api, config, selected_spinner, show_w, use_w)
                        if spinner_action == "quit":
                            running = False
                        else:
                            # Reinit display and fonts after spinner closed its window
                            screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
                            pygame.display.set_caption("Spinbot")
                            fonts = v.get_fonts()
                            state = "main"
                        break

        elif state == "theme_select":
            _draw_page_title(screen, fonts, "Select Theme")
            buttons = _get_theme_buttons(fonts)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "back":
                        state = "main"
                    elif btn.tag:
                        v.set_theme(btn.tag)
                        if config is None:
                            config = {}
                        config["theme"] = btn.tag
                        save_config(config)
                        status_message = f"Theme: {v.get_theme()['name']}"
                        status_timer = 2.0
                        state = "main"

        if running:
            pygame.display.flip()

    pygame.quit()


def _save_and_apply_config(new_config, old_config):
    """Preserve theme from old config."""
    if old_config:
        if old_config.get("theme"):
            new_config["theme"] = old_config["theme"]
        if old_config.get("custom_theme"):
            new_config["custom_theme"] = old_config["custom_theme"]


def _run_spinner(api, config, spinner_idx, show_weights, use_weights):
    """Run the selected spinner. Returns 'menu' or 'quit'."""
    entries = build_entries(api, config)
    if not entries:
        return "menu"

    if not use_weights:
        entries = [(name, 1) for name, _ in entries]

    _, _, module_name, func_name = SPINNERS[spinner_idx]

    def on_winner(name):
        try:
            api.send_chat(f"Congratulations @{name}, you won the giveaway!")
        except Exception:
            pass

    module = importlib.import_module(module_name)
    run_fn = getattr(module, func_name)
    _winner_name, action = run_fn(entries, on_winner=on_winner, show_weights=show_weights)
    return action


def _draw_main_menu(screen, fonts, config, mouse_pos, clicked, set_state, api, status_msg):
    """Draw main menu header."""
    title = fonts["large"].render("SPINBOT", True, v.ACCENT_COLOR)
    screen.blit(title, title.get_rect(center=(v.WIDTH // 2, 40)))

    # Config summary
    y = 75
    if config and config.get("mode"):
        mode = config.get("mode", "currency")
        if mode == "currency":
            info = f"Currency: {config.get('checkin_currency_name', '?')}"
            bonus = config.get("bonus_currency_name")
            if bonus:
                info += f"  |  Bonus: {bonus} (+{config.get('bonus_weight', 0)})"
        else:
            info = f"Metadata: {config.get('checkin_metadata_key', '?')}"
        text = fonts["hint"].render(info, True, v.DIM_TEXT)
        screen.blit(text, text.get_rect(center=(v.WIDTH // 2, y)))
    else:
        text = fonts["hint"].render("Not configured - click Configure to set up", True, v.ACCENT_COLOR)
        screen.blit(text, text.get_rect(center=(v.WIDTH // 2, y)))

    if status_msg:
        msg = fonts["medium"].render(status_msg, True, v.ACCENT_COLOR)
        screen.blit(msg, msg.get_rect(center=(v.WIDTH // 2, v.HEIGHT - 30)))


def _get_main_buttons(fonts, config):
    """Build main menu buttons."""
    buttons = []
    btn_w = 180
    btn_h = 45
    gap = 10
    cols = 2
    start_x = (v.WIDTH - (cols * btn_w + (cols - 1) * gap)) // 2
    start_y = 105

    for i, (key, label, _, _) in enumerate(SPINNERS):
        col = i % cols
        row = i // cols
        x = start_x + col * (btn_w + gap)
        y = start_y + row * (btn_h + gap)
        buttons.append(Button((x, y, btn_w, btn_h), label, fonts["small"], tag=f"spinner_{i}"))

    # Bottom buttons
    bottom_y = start_y + (len(SPINNERS) // cols + 1) * (btn_h + gap) + 20
    settings_w = 250
    settings_gap = 15
    total_settings_w = settings_w * 3 + settings_gap * 2
    sx = (v.WIDTH - total_settings_w) // 2

    buttons.append(Button((sx, bottom_y, settings_w, btn_h), "Configure Currencies", fonts["small"],
                          color=v.PANEL_BG, tag="configure"))
    buttons.append(Button((sx + settings_w + settings_gap, bottom_y, settings_w, btn_h),
                          f"Theme: {v.get_theme()['name']}", fonts["small"],
                          color=v.PANEL_BG, tag="theme"))
    buttons.append(Button((sx + 2 * (settings_w + settings_gap), bottom_y, settings_w, btn_h),
                          "Quit", fonts["small"], color=v.PANEL_BG, tag="quit"))

    return buttons


def _draw_page_title(screen, fonts, title):
    text = fonts["large"].render(title, True, v.ACCENT_COLOR)
    screen.blit(text, text.get_rect(center=(v.WIDTH // 2, 40)))


def _get_config_mode_buttons(fonts):
    btn_w = 300
    btn_h = 50
    cx = v.WIDTH // 2
    return [
        Button((cx - btn_w // 2, 200, btn_w, btn_h), "Currency (most common)", fonts["medium"], tag="currency"),
        Button((cx - btn_w // 2, 270, btn_w, btn_h), "User Metadata", fonts["medium"], tag="metadata"),
        Button((cx - btn_w // 2, 380, btn_w, btn_h), "Back", fonts["medium"], tag="back"),
    ]


def _draw_config_mode(screen, fonts, mouse_pos, clicked, config_temp, set_state):
    _draw_page_title(screen, fonts, "How do you track check-ins?")


def _get_currency_buttons(fonts, currencies):
    buttons = []
    btn_w = 300
    btn_h = 50
    cx = v.WIDTH // 2
    y = 150
    for cid, cconfig in (currencies or {}).items():
        name = cconfig["name"]
        buttons.append(Button((cx - btn_w // 2, y, btn_w, btn_h), name, fonts["medium"],
                              tag=f"{cid}|{name}"))
        y += 65
    buttons.append(Button((cx - btn_w // 2, y + 30, btn_w, btn_h), "Back", fonts["medium"], tag="back"))
    return buttons


def _get_bonus_buttons(fonts, currencies, checkin_id):
    buttons = []
    btn_w = 300
    btn_h = 50
    cx = v.WIDTH // 2
    y = 150

    hint_font = fonts["hint"]
    # We'll draw hint text in the caller; buttons only here
    for cid, cconfig in (currencies or {}).items():
        if cid == checkin_id:
            continue
        name = cconfig["name"]
        buttons.append(Button((cx - btn_w // 2, y, btn_w, btn_h), name, fonts["medium"],
                              tag=f"{cid}|{name}"))
        y += 65

    buttons.append(Button((cx - btn_w // 2, y + 20, btn_w, btn_h), "Skip (no bonus)", fonts["medium"], tag="skip"))
    buttons.append(Button((cx - btn_w // 2, y + 85, btn_w, btn_h), "Back", fonts["medium"], tag="back"))
    return buttons


def _draw_text_input(screen, fonts, label, text):
    _draw_page_title(screen, fonts, label)
    # Input box
    box_rect = pygame.Rect(v.WIDTH // 2 - 200, 300, 400, 50)
    pygame.draw.rect(screen, v.PANEL_BG, box_rect, border_radius=8)
    pygame.draw.rect(screen, v.ACCENT_COLOR, box_rect, 2, border_radius=8)
    text_surf = fonts["medium"].render(text + "|", True, v.TEXT_COLOR)
    screen.blit(text_surf, text_surf.get_rect(midleft=(box_rect.left + 15, box_rect.centery)))


def _get_odds_buttons(fonts):
    buttons = []
    btn_w = 350
    btn_h = 50
    cx = v.WIDTH // 2
    y = 150
    for i, (label, _, _) in enumerate(ODDS_MODES):
        buttons.append(Button((cx - btn_w // 2, y, btn_w, btn_h), label, fonts["medium"], tag=str(i)))
        y += 65
    buttons.append(Button((cx - btn_w // 2, y + 30, btn_w, btn_h), "Back", fonts["medium"], tag="back"))
    return buttons


def _get_theme_buttons(fonts):
    buttons = []
    btn_w = 300
    btn_h = 45
    cx = v.WIDTH // 2
    y = 120
    for key, theme in v.THEMES.items():
        name = theme["name"]
        active = v.get_theme()["name"] == name
        color = v.ACCENT_COLOR if active else v.PANEL_BG
        text_color = v.BG_COLOR if active else v.TEXT_COLOR
        buttons.append(Button((cx - btn_w // 2, y, btn_w, btn_h), name, fonts["medium"],
                              color=color, text_color=text_color, tag=key))
        y += 55
    buttons.append(Button((cx - btn_w // 2, y + 20, btn_w, btn_h), "Back", fonts["medium"], tag="back"))
    return buttons


def _set_state_holder(loc, new_state):
    """Helper to set state from nested scope."""
    pass


def _apply_state(loc, new_state):
    pass
