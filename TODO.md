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

## Bot Platforms
- [x] Firebot support (REST API at localhost:7472)
- [x] Streamer.bot support (WebSocket API at ws://127.0.0.1:8080/)
- [x] Bot platform selection in config flow

## Features
- [x] Currency-based entry tracking (Firebot)
- [x] Metadata-based entry tracking (Firebot)
- [x] User global variable tracking (Streamer.bot)
- [x] Bonus currency/metadata/variable for first check-in
- [x] Persistent config (~/.spinbot/config.json)
- [x] Announce winner in Twitch chat via Firebot or Streamer.bot
- [x] Selectable spinner types (8 total)
- [x] Selectable themes (5 presets + custom)
- [x] Standalone .exe packaging
- [x] Streamer excluded from own giveaways
- [x] Wiki and issue templates

---

## v2.0 — Twitch Integration
- [ ] Direct Twitch connection (IRC / EventSub)
- [ ] `!enter` raffle mode — viewers type !enter in Twitch chat to join
- [ ] Open/close raffle flow in the UI
- [ ] Eligibility filters (configurable, stackable):
  - [ ] Followers only — must be following the channel
  - [ ] Subscribers only — must be an active sub
  - [ ] Both — must be following AND subscribed
- [ ] Entry pool shared between check-in mode and !enter mode (or separate)

## v3.0 — Discord Integration
- [ ] Discord bot connection
- [ ] `!enter` in a configured Discord channel
- [ ] Cross-platform entry pool — Twitch + Discord entries combined into one giveaway
- [ ] Configurable which Discord channel(s) to listen in
- [ ] Winner announced in both Twitch chat and Discord
