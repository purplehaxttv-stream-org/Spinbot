"""Twitch Helix API and IRC chat client for Spinbot."""
import socket
import threading
import time

import requests


class TwitchAPI:
    """Twitch Helix API client for follower/subscriber checks."""

    HELIX_URL = "https://api.twitch.tv/helix"

    def __init__(self, client_id, access_token, broadcaster_id):
        self.client_id = client_id
        self.access_token = access_token
        self.broadcaster_id = broadcaster_id
        self._headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}",
        }

    def is_follower(self, user_id):
        """Check if a user follows the broadcaster."""
        resp = requests.get(
            f"{self.HELIX_URL}/channels/followers",
            headers=self._headers,
            params={
                "broadcaster_id": self.broadcaster_id,
                "user_id": user_id,
            },
        )
        if resp.status_code == 200:
            return resp.json().get("total", 0) > 0
        return False

    def is_subscriber(self, user_id):
        """Check if a user is subscribed to the broadcaster."""
        resp = requests.get(
            f"{self.HELIX_URL}/subscriptions/user",
            headers=self._headers,
            params={
                "broadcaster_id": self.broadcaster_id,
                "user_id": user_id,
            },
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            return len(data) > 0
        return False

    def get_user(self, login):
        """Look up a user by login name. Returns dict with id, login, display_name."""
        resp = requests.get(
            f"{self.HELIX_URL}/users",
            headers=self._headers,
            params={"login": login},
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                return data[0]
        return None

    def get_users_by_id(self, user_ids):
        """Look up users by ID. Returns list of user dicts."""
        if not user_ids:
            return []
        results = []
        # Helix allows up to 100 per request
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i:i + 100]
            resp = requests.get(
                f"{self.HELIX_URL}/users",
                headers=self._headers,
                params=[("id", uid) for uid in batch],
            )
            if resp.status_code == 200:
                results.extend(resp.json().get("data", []))
        return results


class TwitchChat:
    """Twitch IRC client that listens for commands in chat."""

    IRC_HOST = "irc.chat.twitch.tv"
    IRC_PORT = 6667

    def __init__(self, access_token, nick, channel):
        self.access_token = access_token
        self.nick = nick.lower()
        self.channel = f"#{channel.lower()}"
        self._sock = None
        self._running = False
        self._connected = False
        self._thread = None
        self._entries = {}  # user_id -> display_name
        self._lock = threading.Lock()
        self._on_entry = None

    def start(self, on_entry=None):
        """Connect to IRC and start listening in a background thread."""
        self._on_entry = on_entry
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Disconnect from IRC."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def get_entries(self):
        """Return a copy of current entries {user_id: display_name}."""
        with self._lock:
            return dict(self._entries)

    def clear_entries(self):
        """Clear all collected entries."""
        with self._lock:
            self._entries.clear()

    @property
    def entry_count(self):
        with self._lock:
            return len(self._entries)

    def _run(self):
        """IRC listener loop."""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5)
            self._sock.connect((self.IRC_HOST, self.IRC_PORT))

            # Request tags before JOIN so user-id/display-name are available immediately
            self._send("CAP REQ :twitch.tv/tags")
            self._send(f"PASS oauth:{self.access_token}")
            self._send(f"NICK {self.nick}")
            self._send(f"JOIN {self.channel}")

            buffer = ""
            while self._running:
                try:
                    data = self._sock.recv(4096).decode("utf-8", errors="replace")
                    if not data:
                        break
                    buffer += data
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        self._handle_line(line)
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass

    def _send(self, msg):
        self._sock.sendall(f"{msg}\r\n".encode("utf-8"))

    def _handle_line(self, line):
        # Respond to PING
        if line.startswith("PING"):
            self._send(f"PONG{line[4:]}")
            return

        # Mark connected after CAP ACK (tags are now active)
        if "CAP * ACK" in line:
            self._connected = True
            return

        # Parse PRIVMSG with tags
        if "PRIVMSG" not in line:
            return

        # Extract tags
        tags = {}
        if line.startswith("@"):
            tag_str, line = line.split(" ", 1)
            for pair in tag_str[1:].split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    tags[k] = v

        # Check if it's a !enter command
        parts = line.split(" ", 3)
        if len(parts) < 4:
            return
        message = parts[3].lstrip(":").strip().lower()

        if message.split()[0] == "!enter" if message.split() else False:
            user_id = tags.get("user-id", "")
            display_name = tags.get("display-name", "")
            # Fall back to parsing nick from prefix
            prefix = parts[0]
            if "!" in prefix:
                nick = prefix.split("!")[0].lstrip(":")
                if not display_name:
                    display_name = nick
                if not user_id:
                    user_id = nick  # Use login as ID fallback

            if user_id and display_name:
                with self._lock:
                    # Check both user_id and display_name to prevent duplicates
                    # (first !enter may use nick as ID, second may use numeric ID)
                    if user_id not in self._entries and display_name not in self._entries.values():
                        self._entries[user_id] = display_name
                        if self._on_entry:
                            self._on_entry(user_id, display_name)

    def send_message(self, message):
        """Send a chat message to the channel."""
        if self._sock:
            self._send(f"PRIVMSG {self.channel} :{message}")
