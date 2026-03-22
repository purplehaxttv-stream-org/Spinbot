"""Main GUI application - all menus and navigation in pygame."""
import importlib
import threading

import pygame

import spinbot.visuals as v
from spinbot.firebot import FirebotAPI
from spinbot.streamerbot import StreamerbotAPI
from spinbot.twitch_auth import start_device_flow, poll_for_token, validate_token, refresh_token
from spinbot.twitch import TwitchAPI, TwitchChat
from spinbot.config import load_config, save_config

TWITCH_CLIENT_ID = "REMOVED"
TWITCH_CLIENT_SECRET = "REMOVED"

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


def _build_entries_streamerbot(api, config):
    variable_name = config.get("sb_variable_name", "")
    bonus_variable = config.get("sb_bonus_variable")
    bonus_weight = config.get("bonus_weight", 0)
    entries = []
    variables = api.get_user_globals(variable_name)
    bonus_map = {}
    if bonus_variable:
        bonus_vars = api.get_user_globals(bonus_variable)
        for var in bonus_vars:
            uid = var.get("userName") or var.get("userId", "")
            try:
                bonus_map[uid] = int(var.get("value", 0))
            except (ValueError, TypeError):
                pass
    for var in variables:
        uid = var.get("userName") or var.get("userId", "")
        if not uid:
            continue
        try:
            checkins = int(var.get("value", 0))
        except (ValueError, TypeError):
            continue
        bonus = bonus_map.get(uid, 0) * bonus_weight if bonus_variable else 0
        total = checkins + bonus
        if total > 0:
            entries.append((uid, total))
    return entries


def build_entries(api, config):
    """Fetch viewer data and return a list of (name, weight) entry tuples."""
    bot_type = config.get("bot_type", "firebot")
    if bot_type == "streamerbot":
        entries = _build_entries_streamerbot(api, config)
    elif config.get("mode") == "metadata":
        entries = _build_entries_metadata(api, config)
    else:
        entries = _build_entries_currency(api, config)
    exclude = config.get("streamer_name", "").lower()
    if exclude:
        entries = [(name, w) for name, w in entries if name.lower() != exclude]
    return entries


def _create_api(config):
    """Create the appropriate API client based on config."""
    if config and config.get("bot_type") == "streamerbot":
        url = config.get("sb_url", "ws://127.0.0.1:8080/")
        return StreamerbotAPI(url=url)
    return FirebotAPI()


def run_app():
    """Launch the main Spinbot GUI loop."""
    config = load_config()
    api = _create_api(config)

    if config:
        if config.get("custom_theme"):
            v.THEMES["custom"] = config["custom_theme"]
        if config.get("theme"):
            v.set_theme(config["theme"])

    pygame.init()
    screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
    pygame.display.set_caption("Spinbot")
    clock = pygame.time.Clock()

    state = "main"  # main, config_bot, config_mode, config_currency, config_bonus,
                     # config_bonus_weight, config_meta_key, config_sb_variable,
                     # config_sb_bonus, config_sb_bonus_weight,
                     # spinner_select, odds_select, theme_select,
                     # twitch_auth, raffle_setup, raffle_active, raffle_spinner
    selected_spinner = None
    status_message = ""
    status_timer = 0

    # For config flow
    config_temp = {}
    currencies_cache = None
    input_text = ""
    input_label = ""
    input_callback = None

    # For Twitch raffle
    twitch_chat = None
    twitch_api = None
    twitch_auth_code = None
    twitch_auth_device = None
    twitch_auth_thread = None
    twitch_auth_result = None
    raffle_filter = "anyone"  # anyone, followers, subscribers, both

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
                        state = "config_bot"
                    elif btn.tag == "theme":
                        state = "theme_select"
                    elif btn.tag == "quit":
                        running = False
                    elif btn.tag == "raffle":
                        # Check if we have a valid Twitch token
                        token = config.get("twitch_access_token") if config else None
                        if token and validate_token(token):
                            state = "raffle_setup"
                        elif token and config.get("twitch_refresh_token"):
                            # Try refreshing
                            new_tokens = refresh_token(
                                TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET,
                                config["twitch_refresh_token"])
                            if new_tokens:
                                config["twitch_access_token"] = new_tokens["access_token"]
                                if new_tokens.get("refresh_token"):
                                    config["twitch_refresh_token"] = new_tokens["refresh_token"]
                                save_config(config)
                                state = "raffle_setup"
                            else:
                                state = "twitch_auth"
                        else:
                            state = "twitch_auth"
                    elif btn.tag and btn.tag.startswith("spinner_"):
                        idx = int(btn.tag.split("_")[1])
                        if config and (config.get("mode") or config.get("sb_variable_name")):
                            selected_spinner = idx
                            state = "odds_select"
                        else:
                            status_message = "Run Configure first!"
                            status_timer = 2.0

        elif state == "config_bot":
            _draw_page_title(screen, fonts, "Select Your Bot Platform")
            buttons = _get_bot_select_buttons(fonts)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "firebot":
                        config_temp = {"bot_type": "firebot"}
                        state = "config_streamer_name"
                        input_text = config.get("streamer_name", "") if config else ""
                        input_label = "Your Twitch username (excluded from giveaways):"
                    elif btn.tag == "streamerbot":
                        config_temp = {"bot_type": "streamerbot"}
                        state = "config_streamer_name"
                        input_text = config.get("streamer_name", "") if config else ""
                        input_label = "Your Twitch username (excluded from giveaways):"
                    elif btn.tag == "back":
                        state = "main"

        elif state == "config_streamer_name":
            _draw_text_input(screen, fonts, input_label, input_text)
            confirm_btn = Button((v.WIDTH // 2 - 60, 400, 120, 40), "Confirm", fonts["medium"],
                                 color=v.ACCENT_COLOR, text_color=v.BG_COLOR)
            confirm_btn.check_hover(mouse_pos)
            confirm_btn.draw(screen)
            back_btn = Button((v.WIDTH // 2 - 60, 460, 120, 40), "Back", fonts["medium"])
            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)
            if clicked:
                if confirm_btn.check_click(clicked):
                    config_temp["streamer_name"] = input_text.strip()
                    if config_temp["bot_type"] == "firebot":
                        state = "config_mode"
                        try:
                            fb = FirebotAPI()
                            currencies_cache = fb.get_currencies()
                        except Exception:
                            currencies_cache = {}
                    else:
                        state = "config_sb_variable"
                        input_text = ""
                        input_label = "Enter user global variable for check-ins:"
                elif back_btn.check_click(clicked):
                    state = "config_bot"
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        config_temp["streamer_name"] = input_text.strip()
                        if config_temp["bot_type"] == "firebot":
                            state = "config_mode"
                            try:
                                fb = FirebotAPI()
                                currencies_cache = fb.get_currencies()
                            except Exception:
                                currencies_cache = {}
                        else:
                            state = "config_sb_variable"
                            input_text = ""
                            input_label = "Enter user global variable for check-ins:"
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        elif state == "config_mode":
            _draw_config_mode(screen, fonts, mouse_pos, clicked, config_temp,
                              lambda s: _apply_state(locals(), s))
            buttons = _get_config_mode_buttons(fonts)
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "currency":
                        config_temp["mode"] = "currency"
                        state = "config_currency"
                    elif btn.tag == "metadata":
                        config_temp["mode"] = "metadata"
                        state = "config_meta_key"
                        input_text = ""
                        input_label = "Enter metadata key for check-ins:"
                    elif btn.tag == "back":
                        state = "config_bot"

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
                        api = _create_api(config)
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
                    api = _create_api(config)
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
                        api = _create_api(config)
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
                    api = _create_api(config)
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
                        api = _create_api(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        elif state == "config_sb_variable":
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
                    config_temp["sb_variable_name"] = input_text
                    state = "config_sb_bonus"
                elif back_btn.check_click(clicked):
                    state = "config_bot"
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text:
                        config_temp["sb_variable_name"] = input_text
                        state = "config_sb_bonus"
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        elif state == "config_sb_bonus":
            _draw_page_title(screen, fonts, "Bonus Variable (optional)")
            hint = fonts["hint"].render(
                "Add a separate variable for first check-in bonuses?", True, v.DIM_TEXT)
            screen.blit(hint, hint.get_rect(center=(v.WIDTH // 2, 90)))
            btn_w, btn_h = 300, 50
            cx = v.WIDTH // 2
            yes_btn = Button((cx - btn_w // 2, 200, btn_w, btn_h), "Yes, add bonus variable",
                             fonts["medium"], tag="yes")
            skip_btn = Button((cx - btn_w // 2, 270, btn_w, btn_h), "Skip (no bonus)",
                              fonts["medium"], tag="skip")
            back_btn = Button((cx - btn_w // 2, 380, btn_w, btn_h), "Back",
                              fonts["medium"], tag="back")
            for btn in [yes_btn, skip_btn, back_btn]:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    if btn.tag == "yes":
                        state = "config_sb_bonus_var"
                        input_text = ""
                        input_label = "Enter bonus variable name:"
                    elif btn.tag == "skip":
                        config_temp["sb_bonus_variable"] = None
                        config_temp["bonus_weight"] = 0
                        _save_and_apply_config(config_temp, config)
                        config = config_temp
                        save_config(config)
                        api = _create_api(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif btn.tag == "back":
                        state = "config_sb_variable"
                        input_text = config_temp.get("sb_variable_name", "")
                        input_label = "Enter user global variable for check-ins:"

        elif state == "config_sb_bonus_var":
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
                    config_temp["sb_bonus_variable"] = input_text
                    state = "config_sb_bonus_weight"
                    input_text = "1"
                    input_label = "Extra entries per first check-in:"
                elif back_btn.check_click(clicked):
                    state = "config_sb_bonus"
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text:
                        config_temp["sb_bonus_variable"] = input_text
                        state = "config_sb_bonus_weight"
                        input_text = "1"
                        input_label = "Extra entries per first check-in:"
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and len(input_text) < 30:
                        input_text += event.unicode

        elif state == "config_sb_bonus_weight":
            _draw_text_input(screen, fonts, input_label, input_text)
            confirm_btn = Button((v.WIDTH // 2 - 60, 400, 120, 40), "Confirm", fonts["medium"],
                                 color=v.ACCENT_COLOR, text_color=v.BG_COLOR)
            confirm_btn.check_hover(mouse_pos)
            confirm_btn.draw(screen)
            if clicked:
                if confirm_btn.check_click(clicked):
                    try:
                        config_temp["bonus_weight"] = int(input_text) if input_text else 1
                    except ValueError:
                        config_temp["bonus_weight"] = 1
                    _save_and_apply_config(config_temp, config)
                    config = config_temp
                    save_config(config)
                    api = _create_api(config)
                    state = "main"
                    status_message = "Configuration saved!"
                    status_timer = 2.0
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
                        api = _create_api(config)
                        state = "main"
                        status_message = "Configuration saved!"
                        status_timer = 2.0
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode and event.unicode.isdigit() and len(input_text) < 5:
                        input_text += event.unicode

        elif state == "twitch_auth":
            _draw_page_title(screen, fonts, "Connect Twitch Account")
            if twitch_auth_thread is None:
                # Start the device flow
                try:
                    flow = start_device_flow(TWITCH_CLIENT_ID)
                    twitch_auth_code = flow["user_code"]
                    twitch_auth_device = flow["device_code"]
                    interval = flow.get("interval", 5)
                    expires = flow.get("expires_in", 300)
                    import webbrowser
                    webbrowser.open(flow["verification_uri"])
                    twitch_auth_result = None

                    def _poll():
                        nonlocal twitch_auth_result
                        twitch_auth_result = poll_for_token(
                            TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET,
                            twitch_auth_device, interval, expires)

                    twitch_auth_thread = threading.Thread(target=_poll, daemon=True)
                    twitch_auth_thread.start()
                except Exception:
                    status_message = "Failed to start Twitch auth"
                    status_timer = 3.0
                    twitch_auth_thread = None
                    state = "main"

            if twitch_auth_thread is not None:
                # Show the code
                msg1 = fonts["medium"].render("A browser window has opened.", True, v.TEXT_COLOR)
                screen.blit(msg1, msg1.get_rect(center=(v.WIDTH // 2, 150)))
                msg2 = fonts["medium"].render("Enter this code on Twitch:", True, v.TEXT_COLOR)
                screen.blit(msg2, msg2.get_rect(center=(v.WIDTH // 2, 200)))
                code_text = fonts["large"].render(twitch_auth_code or "...", True, v.ACCENT_COLOR)
                screen.blit(code_text, code_text.get_rect(center=(v.WIDTH // 2, 260)))
                hint = fonts["hint"].render("Waiting for authorization...", True, v.DIM_TEXT)
                screen.blit(hint, hint.get_rect(center=(v.WIDTH // 2, 320)))

                back_btn = Button((v.WIDTH // 2 - 60, 400, 120, 40), "Cancel", fonts["medium"])
                back_btn.check_hover(mouse_pos)
                back_btn.draw(screen)
                if clicked and back_btn.check_click(clicked):
                    twitch_auth_thread = None
                    state = "main"

                # Check if auth completed
                if not twitch_auth_thread.is_alive():
                    if twitch_auth_result:
                        token = twitch_auth_result["access_token"]
                        user_info = validate_token(token)
                        if config is None:
                            config = {}
                        config["twitch_access_token"] = token
                        config["twitch_refresh_token"] = twitch_auth_result.get("refresh_token")
                        config["twitch_login"] = user_info.get("login", "") if user_info else ""
                        config["twitch_user_id"] = user_info.get("user_id", "") if user_info else ""
                        if not config.get("streamer_name"):
                            config["streamer_name"] = config["twitch_login"]
                        save_config(config)
                        status_message = f"Connected as {config['twitch_login']}!"
                        status_timer = 2.0
                        state = "raffle_setup"
                    else:
                        status_message = "Authorization failed or timed out"
                        status_timer = 3.0
                        state = "main"
                    twitch_auth_thread = None

        elif state == "raffle_setup":
            _draw_page_title(screen, fonts, "Raffle Setup")
            login = config.get("twitch_login", "?") if config else "?"
            info = fonts["hint"].render(f"Connected as: {login}", True, v.DIM_TEXT)
            screen.blit(info, info.get_rect(center=(v.WIDTH // 2, 80)))

            label = fonts["medium"].render("Who can enter?", True, v.TEXT_COLOR)
            screen.blit(label, label.get_rect(center=(v.WIDTH // 2, 140)))

            filter_options = [
                ("Anyone", "anyone"),
                ("Followers Only", "followers"),
                ("Subscribers Only", "subscribers"),
                ("Followers + Subscribers", "both"),
            ]
            btn_w, btn_h = 300, 45
            cx = v.WIDTH // 2
            y = 180
            for filter_label, filter_tag in filter_options:
                active = raffle_filter == filter_tag
                color = v.ACCENT_COLOR if active else v.PANEL_BG
                text_color = v.BG_COLOR if active else v.TEXT_COLOR
                btn = Button((cx - btn_w // 2, y, btn_w, btn_h), filter_label,
                             fonts["medium"], color=color, text_color=text_color, tag=filter_tag)
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    raffle_filter = filter_tag
                y += 55

            start_btn = Button((cx - btn_w // 2, y + 20, btn_w, btn_h), "Open Raffle",
                               fonts["medium"], color=v.ACCENT_COLOR, text_color=v.BG_COLOR,
                               tag="start")
            start_btn.check_hover(mouse_pos)
            start_btn.draw(screen)
            back_btn = Button((cx - btn_w // 2, y + 80, btn_w, btn_h), "Back",
                              fonts["medium"], tag="back")
            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)

            if clicked:
                if start_btn.check_click(clicked):
                    # Start listening for !enter
                    token = config.get("twitch_access_token", "")
                    login = config.get("twitch_login", "")
                    twitch_chat = TwitchChat(token, login, login)
                    twitch_chat.start()
                    twitch_api = TwitchAPI(
                        TWITCH_CLIENT_ID, token,
                        config.get("twitch_user_id", ""))
                    state = "raffle_active"
                elif back_btn.check_click(clicked):
                    state = "main"

        elif state == "raffle_active":
            _draw_page_title(screen, fonts, "Raffle Open — !enter in chat")
            count = twitch_chat.entry_count if twitch_chat else 0
            count_text = fonts["large"].render(str(count), True, v.ACCENT_COLOR)
            screen.blit(count_text, count_text.get_rect(center=(v.WIDTH // 2, 160)))
            count_label = fonts["medium"].render("entries", True, v.DIM_TEXT)
            screen.blit(count_label, count_label.get_rect(center=(v.WIDTH // 2, 210)))

            filter_labels = {
                "anyone": "Anyone can enter",
                "followers": "Followers only",
                "subscribers": "Subscribers only",
                "both": "Followers + Subscribers only",
            }
            filter_text = fonts["hint"].render(filter_labels.get(raffle_filter, ""), True, v.DIM_TEXT)
            screen.blit(filter_text, filter_text.get_rect(center=(v.WIDTH // 2, 260)))

            btn_w, btn_h = 300, 50
            cx = v.WIDTH // 2
            close_btn = Button((cx - btn_w // 2, 320, btn_w, btn_h), "Close Entries & Spin",
                               fonts["medium"], color=v.ACCENT_COLOR, text_color=v.BG_COLOR,
                               tag="close")
            close_btn.check_hover(mouse_pos)
            close_btn.draw(screen)
            cancel_btn = Button((cx - btn_w // 2, 390, btn_w, btn_h), "Cancel Raffle",
                                fonts["medium"], tag="cancel")
            cancel_btn.check_hover(mouse_pos)
            cancel_btn.draw(screen)

            if clicked:
                if close_btn.check_click(clicked) and count > 0:
                    if twitch_chat:
                        twitch_chat.stop()
                    state = "raffle_spinner"
                elif cancel_btn.check_click(clicked):
                    if twitch_chat:
                        twitch_chat.stop()
                        twitch_chat.clear_entries()
                    state = "main"

        elif state == "raffle_spinner":
            _draw_page_title(screen, fonts, "Pick a Spinner")
            count = twitch_chat.entry_count if twitch_chat else 0
            info = fonts["hint"].render(f"{count} entries collected", True, v.DIM_TEXT)
            screen.blit(info, info.get_rect(center=(v.WIDTH // 2, 80)))

            btn_w, btn_h = 180, 45
            gap = 10
            cols = 2
            start_x = (v.WIDTH - (cols * btn_w + (cols - 1) * gap)) // 2
            start_y = 120
            for i, (key, label, _, _) in enumerate(SPINNERS):
                col = i % cols
                row = i // cols
                x = start_x + col * (btn_w + gap)
                y = start_y + row * (btn_h + gap)
                btn = Button((x, y, btn_w, btn_h), label, fonts["small"], tag=f"raffle_spin_{i}")
                btn.check_hover(mouse_pos)
                btn.draw(screen)
                if clicked and btn.check_click(clicked):
                    raffle_spin_idx = i
                    break
            else:
                raffle_spin_idx = None

            if raffle_spin_idx is not None:
                selected_spinner = raffle_spin_idx
                # Build entries from raffle, apply filters
                raw_entries = twitch_chat.get_entries() if twitch_chat else {}
                streamer_id = config.get("twitch_user_id", "") if config else ""
                entries = []
                for user_id, display_name in raw_entries.items():
                    if user_id == streamer_id:
                        continue
                    if raffle_filter in ("followers", "both"):
                        if twitch_api and not twitch_api.is_follower(user_id):
                            continue
                    if raffle_filter in ("subscribers", "both"):
                        if twitch_api and not twitch_api.is_subscriber(user_id):
                            continue
                    entries.append((display_name, 1))
                if not entries:
                    status_message = "No eligible entries after filtering!"
                    status_timer = 2.0
                else:
                    # Run the spinner
                    _, _, module_name, func_name = SPINNERS[selected_spinner]

                    def on_winner(name):
                        try:
                            if twitch_chat:
                                twitch_chat.send_message(
                                    f"Congratulations @{name}, you won the giveaway!")
                        except Exception:
                            pass

                    pygame.display.quit()
                    module = importlib.import_module(module_name)
                    run_fn = getattr(module, func_name)
                    _winner, action = run_fn(entries, on_winner=on_winner, show_weights=False)
                    if twitch_chat:
                        twitch_chat.clear_entries()
                    if action == "quit":
                        running = False
                    else:
                        screen = pygame.display.set_mode((v.WIDTH, v.HEIGHT))
                        pygame.display.set_caption("Spinbot")
                        fonts = v.get_fonts()
                        state = "main"

            # Back button below spinners
            back_y = start_y + (len(SPINNERS) // cols) * (btn_h + gap) + 20
            back_btn = Button((v.WIDTH // 2 - 90, back_y, 180, btn_h), "Back",
                              fonts["small"], tag="back")
            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)
            if clicked and back_btn.check_click(clicked):
                # Re-open the raffle
                if twitch_chat:
                    token = config.get("twitch_access_token", "")
                    login = config.get("twitch_login", "")
                    twitch_chat = TwitchChat(token, login, login)
                    twitch_chat.start()
                state = "raffle_active"

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

    if twitch_chat:
        twitch_chat.stop()
    pygame.quit()


def _save_and_apply_config(new_config, old_config):
    """Preserve theme and other persistent settings from old config."""
    if old_config:
        if old_config.get("theme"):
            new_config.setdefault("theme", old_config["theme"])
        if old_config.get("custom_theme"):
            new_config.setdefault("custom_theme", old_config["custom_theme"])


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
    bot_type = config.get("bot_type", "firebot") if config else "firebot"
    bot_label = "Streamer.bot" if bot_type == "streamerbot" else "Firebot"
    if config and (config.get("mode") or config.get("sb_variable_name")):
        if bot_type == "streamerbot":
            info = f"[{bot_label}]  Variable: {config.get('sb_variable_name', '?')}"
            bonus = config.get("sb_bonus_variable")
            if bonus:
                info += f"  |  Bonus: {bonus} (+{config.get('bonus_weight', 0)})"
        elif config.get("mode") == "currency":
            info = f"[{bot_label}]  Currency: {config.get('checkin_currency_name', '?')}"
            bonus = config.get("bonus_currency_name")
            if bonus:
                info += f"  |  Bonus: {bonus} (+{config.get('bonus_weight', 0)})"
        else:
            info = f"[{bot_label}]  Metadata: {config.get('checkin_metadata_key', '?')}"
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

    # Raffle button (full width, accent color)
    raffle_y = start_y + (len(SPINNERS) // cols) * (btn_h + gap) + 10
    raffle_w = btn_w * cols + gap
    buttons.append(Button((start_x, raffle_y, raffle_w, btn_h), "Start Raffle (!enter)",
                          fonts["small"], color=v.ACCENT_COLOR, text_color=v.BG_COLOR, tag="raffle"))

    # Bottom buttons
    bottom_y = raffle_y + btn_h + 20
    settings_w = 250
    settings_gap = 15
    total_settings_w = settings_w * 3 + settings_gap * 2
    sx = (v.WIDTH - total_settings_w) // 2

    buttons.append(Button((sx, bottom_y, settings_w, btn_h), "Configure", fonts["small"],
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


def _get_bot_select_buttons(fonts):
    btn_w = 300
    btn_h = 50
    cx = v.WIDTH // 2
    return [
        Button((cx - btn_w // 2, 200, btn_w, btn_h), "Firebot", fonts["medium"], tag="firebot"),
        Button((cx - btn_w // 2, 270, btn_w, btn_h), "Streamer.bot", fonts["medium"], tag="streamerbot"),
        Button((cx - btn_w // 2, 380, btn_w, btn_h), "Back", fonts["medium"], tag="back"),
    ]


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
