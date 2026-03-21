# Spinbot TODO

## Giveaway Modes
- [x] Check-in based (weighted by currency/metadata)
- [x] Spin menu (weighted visible, weighted hidden, pure random)
- [ ] !enter command based (equal chance raffle)
  - Requires Twitch IRC connection to listen for !enter in chat
  - **Steps to set up Twitch app:**
    1. Go to https://dev.twitch.tv > Console > Applications > Register Your Application
    2. Name: `Spinbot`
    3. OAuth Redirect URL: `http://localhost`
    4. Category: `Chat Bot`
    5. Click Create
    6. Copy the **Client ID** from the app's manage page
    7. Generate and copy the **Client Secret**
    8. Store both in Spinbot config
  - Use device code auth flow (streamer authorizes, no redirect needed)
  - Scope needed: `chat:read`
  - Streamer authorizes with their own account, no bot account required

## Spinners
- [x] Wheel
- [x] Slot Machine
- [x] Card Flip
- [x] Roulette
- [x] Bracket
- [x] Name Cascade
- [x] Tarot Pull
- [x] Spirit Board (planchette spells out winner letter by letter)

## Themes
- [x] Dark (default)
- [x] Midnight Blue
- [x] Ember
- [x] Void
- [x] Neon
- [x] Custom theme builder (hex colors, saved to config)

## Features
- [x] Currency-based entry tracking
- [x] Metadata-based entry tracking
- [x] Bonus currency/metadata for first check-in
- [x] Persistent config (~/.spinbot/config.json)
- [x] Announce winner in Twitch chat via Firebot POST /effects (firebot:chat)
- [x] Selectable spinner types (8 total)
- [x] Selectable themes (5 presets + custom)
- [ ] Standalone .exe packaging
