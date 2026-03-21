# Spinbot

A streamer giveaway tool with animated spinners, powered by [Firebot](https://firebot.app).

Spinbot pulls viewer check-in data from Firebot and runs one of eight animated spinner types to pick a winner. The winner is automatically announced in your Twitch chat.

## Getting Started

### Requirements

- **[Firebot](https://firebot.app)** installed and running (default: `localhost:7472`)
- A Firebot currency or metadata key that tracks viewer check-ins

### Download

Grab the latest `Spinbot.exe` from the [Releases](https://github.com/purplehaxttv-stream-org/Spinbot/releases) page. No installation required -- just download, run, and connect to Firebot.

### First-Time Setup

On first launch, Spinbot walks you through configuration:

1. Choose how you track check-ins (Firebot currency or viewer metadata)
2. Select your check-in currency/key
3. Optionally add a bonus currency for first check-in rewards
4. Pick a spinner, choose your odds mode, and go

<img src="screenshots/setup.gif" width="400">

Settings are saved to `~/.spinbot/config.json` and persist between sessions. Reconfigure any time from the main menu.

## Features

- 8 animated spinner types
- 3 odds modes: weighted visible, weighted hidden, and pure random
- 5 color themes plus custom theme support
- Winner announced in Twitch chat automatically via Firebot
- Persistent configuration saved between sessions

## Spinners

### Wheel
Classic prize wheel that spins and decelerates to a stop.

<img src="screenshots/wheel.gif" width="400">

### Slot Machine
Three reels scroll through names and lock into place one by one.

<img src="screenshots/slots.gif" width="400">

### Card Flip
Cards shuffle, eliminate one by one, and the last card flips to reveal the winner.

<img src="screenshots/cards.gif" width="400">

### Roulette
A glowing ball spins around a roulette track and settles on a name.

<img src="screenshots/roulette.gif" width="400">

### Bracket
Single-elimination tournament bracket reveals round by round.

<img src="screenshots/bracket.gif" width="400">

### Name Cascade
Names cycle rapidly and decelerate until landing on the winner.

<img src="screenshots/cascade.gif" width="400">

### Tarot Pull
Cards fan out, one is drawn from the spread and flipped to reveal the chosen viewer.

<img src="screenshots/tarot.gif" width="400">

### Spirit Board
A planchette glides across a spirit board, spelling out the winner letter by letter.

<img src="screenshots/spiritboard.gif" width="400">

## Themes

Switch themes from the main menu at any time. Your selection is remembered across sessions.

- **Dark** (default)
- **Midnight Blue**
- **Ember**
- **Void**
- **Neon**
- **Custom** -- build your own with hex colors

## Odds Modes

| Mode | Description |
|------|-------------|
| **Weighted (visible)** | Viewers with more check-ins have proportionally larger slices/slots |
| **Weighted (hidden)** | Odds are weighted but visually equal -- keeps it suspenseful |
| **Pure random** | Every entrant has an equal chance regardless of check-ins |

## Roadmap

See [TODO.md](TODO.md) for planned features including `!enter` command support and more.

## Building from Source

For developers or contributors who want to run from source:

```
git clone https://github.com/purplehaxttv-stream-org/Spinbot.git
cd Spinbot

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

Requires **Python 3.14+** and **Windows**. Dependencies: `pygame-ce`, `requests`.

To build the exe yourself:

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name Spinbot main.py
```

The exe will be in the `dist/` folder.

## License

MIT
