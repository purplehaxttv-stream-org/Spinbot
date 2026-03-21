"""Configuration persistence and interactive setup prompts."""
import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".spinbot")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def save_config(config):
    """Write config dict to disk as JSON."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n  Config saved to {CONFIG_FILE}")


def load_config():
    """Load config from disk, or return None if not yet configured."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def prompt_choice(prompt, options, allow_skip=False):
    """Display numbered options and return the selected one."""
    print(f"\n{prompt}\n")
    for i, (label, _) in enumerate(options, 1):
        print(f"  [{i}] {label}")
    if allow_skip:
        print(f"  [0] Skip")

    while True:
        try:
            raw = input("\n> ").strip()
            choice = int(raw)
            if allow_skip and choice == 0:
                return None
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except (ValueError, EOFError):
            pass
        print("Invalid choice, try again.")


def prompt_number(prompt, default=None):
    """Prompt for a number with optional default."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        try:
            raw = input(f"{prompt}{suffix}: ").strip()
            if not raw and default is not None:
                return default
            return int(raw)
        except (ValueError, EOFError):
            print("Please enter a valid number.")


def prompt_text(prompt):
    """Prompt for a text value."""
    while True:
        raw = input(f"{prompt}: ").strip()
        if raw:
            return raw
        print("Please enter a value.")


def setup(api):
    """Interactive setup. Returns config dict."""
    print("=" * 50)
    print("  SPINBOT SETUP")
    print("=" * 50)

    # Choose tracking mode
    mode = prompt_choice(
        "How do you track check-ins?",
        [("Currency (most common)", "currency"), ("User Metadata", "metadata")],
    )
    if not mode:
        return None
    _, tracking_mode = mode

    if tracking_mode == "currency":
        return _setup_currency(api)
    else:
        return _setup_metadata(api)


def _setup_currency(api):
    """Setup using currency-based tracking."""
    currencies = api.get_currencies()
    if not currencies:
        print("No currencies found in Firebot!")
        return None

    options = [(config["name"], cid) for cid, config in currencies.items()]

    selected = prompt_choice("Select your CHECK-IN currency:", options)
    if not selected:
        return None
    checkin_name, checkin_id = selected

    remaining = [(name, cid) for name, cid in options if cid != checkin_id]

    config = {
        "mode": "currency",
        "checkin_currency_name": checkin_name,
        "checkin_currency_id": checkin_id,
        "bonus_currency_name": None,
        "bonus_currency_id": None,
        "bonus_weight": 0,
    }

    if remaining:
        print(f"\nDoes a separate currency track FIRST check-ins (bonus entries)?")
        bonus = prompt_choice(
            "Select your FIRST CHECK-IN bonus currency (or skip):",
            remaining,
            allow_skip=True,
        )
        if bonus:
            bonus_name, bonus_id = bonus
            bonus_weight = prompt_number(
                "\nHow many extra entries per first check-in?", default=1
            )
            config["bonus_currency_name"] = bonus_name
            config["bonus_currency_id"] = bonus_id
            config["bonus_weight"] = bonus_weight

    return config


def _setup_metadata(api):
    """Setup using metadata-based tracking."""
    checkin_key = prompt_text(
        "\nEnter the metadata key used for check-in counts"
    )

    config = {
        "mode": "metadata",
        "checkin_metadata_key": checkin_key,
        "bonus_metadata_key": None,
        "bonus_weight": 0,
    }

    print(f"\nDo you have a separate metadata key for FIRST check-in bonuses?")
    has_bonus = prompt_choice(
        "Add a bonus metadata key?",
        [("Yes", True), ("No", False)],
    )
    if has_bonus and has_bonus[1]:
        config["bonus_metadata_key"] = prompt_text(
            "Enter the bonus metadata key"
        )
        config["bonus_weight"] = prompt_number(
            "\nHow many extra entries per first check-in?", default=1
        )

    return config


def display_config(config):
    """Print the active config summary."""
    print(f"\n{'=' * 50}")
    mode = config.get("mode", "currency")
    print(f"  Tracking mode     : {mode}")

    if mode == "currency":
        print(f"  Check-in currency : {config['checkin_currency_name']}")
        if config.get("bonus_currency_name"):
            print(f"  Bonus currency    : {config['bonus_currency_name']}")
            print(f"  Bonus weight      : +{config['bonus_weight']} entries per first check-in")
        else:
            print(f"  Bonus currency    : None")
    else:
        print(f"  Check-in key      : {config['checkin_metadata_key']}")
        if config.get("bonus_metadata_key"):
            print(f"  Bonus key         : {config['bonus_metadata_key']}")
            print(f"  Bonus weight      : +{config['bonus_weight']} entries per first check-in")
        else:
            print(f"  Bonus key         : None")

    print(f"{'=' * 50}")
