"""Client for the Firebot REST API."""
import requests


class FirebotAPI:
    """Wrapper around the Firebot local API for viewers, currencies, and effects."""
    def __init__(self, base_url="http://localhost:7472/api/v1"):
        self.base_url = base_url

    def get_status(self):
        """Return the current Firebot connection status."""
        resp = requests.get(f"{self.base_url}/status")
        resp.raise_for_status()
        return resp.json()

    def get_currencies(self):
        """Return all configured currencies."""
        resp = requests.get(f"{self.base_url}/currency")
        resp.raise_for_status()
        return resp.json()

    def get_currency_top(self, currency_name):
        """Return the top holders of the given currency."""
        resp = requests.get(f"{self.base_url}/currency/{currency_name}/top")
        resp.raise_for_status()
        return resp.json()

    def get_effects(self):
        """Return all available effects."""
        resp = requests.get(f"{self.base_url}/effects")
        resp.raise_for_status()
        return resp.json()

    def run_effects(self, effects_list, trigger_data=None):
        """Execute a list of effects, optionally with trigger data."""
        payload = {"effects": {"list": effects_list}}
        if trigger_data:
            payload["triggerData"] = trigger_data
        resp = requests.post(f"{self.base_url}/effects", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_viewers(self):
        """Return all known viewers."""
        resp = requests.get(f"{self.base_url}/viewers")
        resp.raise_for_status()
        return resp.json()

    def get_viewer(self, user_id):
        """Return details for a single viewer by ID."""
        resp = requests.get(f"{self.base_url}/viewers/{user_id}")
        resp.raise_for_status()
        return resp.json()

    def get_viewer_metadata(self, user_id, key):
        """Return a single metadata value for a viewer."""
        resp = requests.get(f"{self.base_url}/viewers/{user_id}/metadata/{key}")
        resp.raise_for_status()
        return resp.json()

    def send_chat(self, message):
        """Send a chat message through the bot account."""
        return self.run_effects([{
            "type": "firebot:chat",
            "message": message,
            "chatter": "Bot",
        }])
