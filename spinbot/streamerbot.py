"""Client for the Streamer.bot WebSocket API."""
import json
import uuid

import websocket


class StreamerbotAPI:
    """Wrapper around the Streamer.bot WebSocket API for viewers, variables, and chat."""

    def __init__(self, url="ws://127.0.0.1:8080/"):
        self.url = url

    def _request(self, payload):
        """Send a request and return the response."""
        payload["id"] = str(uuid.uuid4())
        ws = websocket.create_connection(self.url, timeout=10)
        try:
            # Streamer.bot sends a Hello message on connect; consume it first
            hello = json.loads(ws.recv())
            ws.send(json.dumps(payload))
            result = json.loads(ws.recv())
            return result
        finally:
            ws.close()

    def get_active_viewers(self):
        """Return a list of currently active viewers."""
        resp = self._request({"request": "GetActiveViewers"})
        return resp.get("viewers", [])

    def get_user_globals(self, variable_name):
        """Return all users' values for a given global variable."""
        resp = self._request({
            "request": "TwitchGetUserGlobals",
            "variable": variable_name,
        })
        return resp.get("variables", [])

    def get_global(self, variable_name):
        """Return a single global variable value."""
        resp = self._request({
            "request": "GetGlobals",
            "persisted": True,
        })
        variables = resp.get("variables", {})
        if variable_name in variables:
            return variables[variable_name].get("value")
        return None

    def send_chat(self, message):
        """Send a chat message to the broadcaster's Twitch chat."""
        self._request({
            "request": "SendMessage",
            "message": message,
            "platform": "twitch",
            "bot": True,
            "internal": False,
        })

    def do_action(self, action_name, args=None):
        """Execute a Streamer.bot action by name."""
        payload = {
            "request": "DoAction",
            "action": {"name": action_name},
        }
        if args:
            payload["args"] = args
        return self._request(payload)
