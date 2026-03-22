"""Discord webhook integration for Spinbot."""
import requests


def send_winner(webhook_url, winner_name, message=None):
    """Send a winner announcement to a Discord channel via webhook."""
    if message is None:
        message = f"Congratulations **{winner_name}**, you won the giveaway!"
    else:
        message = message.format(winner=winner_name)
    payload = {
        "embeds": [{
            "title": "Giveaway Winner!",
            "description": message,
            "color": 0xFFD700,
        }],
    }
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception:
        pass
