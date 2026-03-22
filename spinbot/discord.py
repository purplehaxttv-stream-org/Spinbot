"""Discord webhook integration for Spinbot."""
import requests


def send_winner(webhook_url, winner_name):
    """Send a winner announcement to a Discord channel via webhook."""
    payload = {
        "embeds": [{
            "title": "Giveaway Winner!",
            "description": f"Congratulations **{winner_name}**, you won the giveaway!",
            "color": 0xFFD700,
        }],
    }
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception:
        pass
