# 🟣 Takoyomi

**Real-time Japanese overlay translator** for Linux (KDE Plasma / Wayland).

Monitors your clipboard for Japanese text, translates it via Google Translate, and displays the result in a frameless blur overlay — always visible, always on top. Supports bidirectional translation: Japanese to your language, or your language to Japanese.

![Overlay](https://i.imgur.com/ZlT3xQ8.png)
*Overlay showing original Japanese text and its translation*

![Settings](https://i.imgur.com/DuXk5V8.png)
*Settings dialog with language, font, accent, and appearance configuration*

---

## Features

- **Live clipboard monitoring** — polls clipboard every 300 ms; detects Japanese text automatically
- **Bidirectional translation** — Japanese → your language, or your language → Japanese
- **Multi-language support** — translate to/from Spanish, English, French, German, and 25+ languages
- **Frameless translucent overlay** — stays in the bottom-right corner, never steals focus
- **KDE Blur integration** — blends into your desktop with configurable dark tint
- **Configurable UI language** — English or Spanish interface
- **Pulsing status indicator** — green/purple dot pulses with a configurable accent colour
- **Sweeping loading line** — animated gradient sweep while Google Translate is working
- **Click-to-copy** — click the translation text to copy it to your clipboard
- **Pet GIF** — optional animated GIF on the right side (paste any `giphy.gif` URL)
- **Custom accent colours** — pick from 7 presets or use the colour picker for any hex
- **Configurable fonts, sizes, opacity, and window width**

---

## Requirements

- **Linux** with **KDE Plasma** (Wayland recommended, X11 works)
- **wl-paste** — must be installed and on `$PATH`
- **Python** ≥ 3.12
- Internet connection for Google Translate API

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/kurojs/takoyomi.git
cd takoyomi

# Virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Launch
./start.sh

# Or run directly
python -m takoyomi
```

### KDE Application Launcher

```bash
cp assets/takoyomi.desktop ~/.local/share/applications/
```

Then search for **"Takoyomi"** in your app launcher.

---

## Usage

### Overlay

| Action | Result |
|---|---|
| Select Japanese text anywhere | The overlay shows the original + translation |
| Click the **top bar** (green dot / status text) | Opens the quick menu |
| Click the **translation text** | Copies the translation to your clipboard |

### Quick Menu (click top bar of overlay)

| Item | Action |
|---|---|
| ⚙ Settings | Open the configuration dialog |
| 🧪 Test | Translate a sample sentence |
| 🔛 Pause / Resume | Toggle clipboard monitoring on/off |
| ✕ Exit | Quit the application |

### System Tray

| Action | Result |
|---|---|
| Left-click tray icon | Show / hide the overlay |

### Settings

Configure accent colour, background colour and opacity, fonts, UI language, target translation language, custom window width, and pet GIF via the Settings dialog.

---

## Development

```bash
pip install -e ".[test]"
python -m takoyomi
pytest tests/
```

---

## License

MIT — see [LICENSE](./LICENSE).
