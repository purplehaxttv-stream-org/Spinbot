"""Twitch OAuth device code flow for Spinbot."""
import time
import webbrowser

import requests

DEVICE_CODE_URL = "https://id.twitch.tv/oauth2/device"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
REVOKE_URL = "https://id.twitch.tv/oauth2/revoke"

SCOPES = "chat:read chat:edit channel:read:subscriptions moderator:read:followers"


def start_device_flow(client_id):
    """Start the device code flow. Returns the device code response."""
    resp = requests.post(DEVICE_CODE_URL, data={
        "client_id": client_id,
        "scopes": SCOPES,
    })
    resp.raise_for_status()
    return resp.json()


def poll_for_token(client_id, client_secret, device_code, interval=5, expires_in=300):
    """Poll Twitch until the user authorizes or the code expires.

    Returns the token response dict on success, None on timeout.
    """
    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.post(TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        data = resp.json()
        if resp.status_code == 200:
            return data
        status = data.get("status", resp.status_code)
        message = data.get("message", "")
        if status == 400 and "authorization_pending" in message:
            continue
        if status == 400 and "slow_down" in message:
            interval += 1
            continue
        # Any other error means we should stop
        break
    return None


def refresh_token(client_id, client_secret, refresh):
    """Refresh an expired access token."""
    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    })
    if resp.status_code == 200:
        return resp.json()
    return None


def validate_token(access_token):
    """Validate an access token. Returns user info dict or None if invalid."""
    resp = requests.get(VALIDATE_URL, headers={
        "Authorization": f"OAuth {access_token}",
    })
    if resp.status_code == 200:
        return resp.json()
    return None


def authorize(client_id, client_secret):
    """Run the full device code auth flow.

    Opens the browser for the user and blocks until authorized.
    Returns (access_token, refresh_token, user_login, user_id) or None.
    """
    flow = start_device_flow(client_id)
    verification_uri = flow["verification_uri"]
    user_code = flow["user_code"]
    device_code = flow["device_code"]
    interval = flow.get("interval", 5)
    expires_in = flow.get("expires_in", 300)

    webbrowser.open(verification_uri)

    token_data = poll_for_token(client_id, client_secret, device_code, interval, expires_in)
    if not token_data:
        return None

    access_token = token_data["access_token"]
    refresh = token_data.get("refresh_token")

    # Validate to get user info
    user_info = validate_token(access_token)
    if not user_info:
        return None

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "login": user_info.get("login", ""),
        "user_id": user_info.get("user_id", ""),
    }
