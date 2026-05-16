# N1 Translator

**Real-time Japanese→Spanish overlay translator** for Linux (KDE Plasma / Wayland).

Monitors your clipboard for Japanese text, translates it via Google Translate, and displays the result in a frameless blur overlay — always visible, always on top. Designed for learners, readers, and anyone working with Japanese text.

![screenshot](./assets/screenshot.png)

---

## Features

- **Live clipboard monitoring** — polls `wl-paste` every 200 ms; detects Japanese text automatically
- **Frameless translucent overlay** — stays in the bottom-right corner, never steals focus
- **KDE Blur integration** — the overlay blends into your desktop with a dark tint (`rgba(8, 8, 14, 215)`)
- **Pulsing status indicator** — green/purple dot pulses with a configurable accent colour
- **Sweeping loading line** — animated gradient sweep while Google Translate is working
- **Auto-expand** — the overlay grows vertically to fit long translations (capped at 600 px)
- **Click-to-copy** — click the translation text to copy it to your clipboard
- **Settings panel** — configure accent colour, fonts, sizes, and custom window width
- **Custom accent colours** — pick from 7 presets or use the 🎨 colour picker for any hex
- **Pet GIF** — optional animated GIF on the right side (paste any `giphy.gif` URL)
- **Translation cache** — repeated text hits the cache, not the network
- **Pause/Resume** — toggle clipboard monitoring from the overlay menu

---

## Requirements

- **Linux** with **KDE Plasma** (Wayland recommended, X11 works)
- **wl-paste** — must be installed and on `$PATH`
- **Python** ≥ 3.12
- Internet connection for Google Translate API

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kurojs/n1-translator.git
cd n1-translator

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Launch (detached from terminal)
./start.sh

# Or run directly
python -m n1_translator
```

---

## Usage

### Overlay

| Action | Result |
|---|---|
| Select Japanese text anywhere | The overlay shows the original + Spanish translation |
| Click the **top bar** (green dot / status text) | Opens the quick menu |
| Click the **translation text** | Copies the translation to your clipboard |

### Quick Menu (click top bar of overlay)

| Item | Action |
|---|---|
| ⚙ Settings | Open the configuration dialog |
| 🧪 Test | Translate a hardcoded sample sentence |
| 🔛 Pause / Resume | Toggle clipboard monitoring on/off |
| ✕ Exit | Quit the application |

### System Tray

| Action | Result |
|---|---|
| Left-click tray icon | Show / hide the overlay |

> **Note:** On KDE Wayland, the tray icon's right-click context menu relies on `StatusNotifierItem` protocol, which has known issues with Qt. The overlay's top-bar menu is the recommended way to access settings.

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| **Accent colour** | `#22c55e` (green) | 7 presets + custom colour picker |
| **Japanese font** | Noto Sans CJK JP | Any installed font |
| **Japanese font size** | 11 pt | 8–32 range |
| **Spanish font** | sans-serif | Any installed font |
| **Spanish font size** | 13 pt | 8–32 range |
| **Custom window width** | Off (420 px) | Override the default width (280–1200 px) |
| **Pet GIF** | Off | Animated GIF on the right side; paste any `https://…giphy.gif` URL |

Settings are persisted via `QSettings` (`~/.config/n1-tools/N1 Translator.conf`).

---

## Project Structure

```
n1-translator/
├── pyproject.toml              # Build metadata & entry point
├── README.md
├── LICENSE
├── requirements.txt            # pip dependencies
├── start.sh                    # Legacy launcher
├── scripts/
│   └── start.sh                # Production launcher (detached)
└── src/
    └── n1_translator/
        ├── __init__.py
        ├── __main__.py          # CLI entry: ``python -m n1_translator``
        ├── app.py               # Application class, tray, clipboard polling
        ├── overlay.py           # Translucent overlay widget & animations
        └── settings.py          # QSettings persistence & settings dialog
```

---

## Development

```bash
# Editable install (reflects changes immediately)
pip install -e .

# Run
python -m n1_translator

# Or via the installed script
n1-translator
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No translation appears | `wl-paste` not installed | `sudo pacman -S wl-clipboard` |
| Overlay looks solid (no blur) | KDE compositor doesn't support blur on this window type | Works on Plasma Wayland out of the box |
| Tray icon right-click doesn't open menu | Known KDE Wayland / Qt bug | Use the overlay top-bar menu instead |
| Google Translate returns errors | Rate limit or network issue | Translations are cached; retry after a few seconds |

---

## License

MIT — see [LICENSE](./LICENSE).
