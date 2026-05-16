# N1 Translator — Installation Guide

Step-by-step instructions to install N1 Translator on **KDE Plasma (Wayland)**.

---

## Prerequisites

- **Arch Linux** (other distros work too, but paths may vary)
- **KDE Plasma** on **Wayland**
- **wl-clipboard** — provides `wl-paste` for clipboard monitoring
- **Python** ≥ 3.12
- **Git**

```bash
# Arch Linux
sudo pacman -S wl-clipboard python python-pip git
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/kurojs/n1-translator.git
cd n1-translator
```

---

## 2. Virtual Environment & Dependencies

The project ships with `scripts/start.sh` which handles everything automatically.
Or you can set it up manually:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install the package in editable mode (makes `n1-translator` command available)
pip install -e .
```

---

## 3. Quick Test

Run the translator to verify everything works:

```bash
# From within the project directory (with venv activated)
python -m n1_translator

# Or use the installed command
n1-translator
```

You should see a translucent overlay appear in the bottom-right corner.
Copy some Japanese text — the overlay will show the Spanish translation.

---

## 4. KDE Application Launcher

To launch N1 Translator from KDE's app menu (Kickoff) or add it to your panel:

```bash
# Copy the desktop file to the applications folder
cp assets/n1-translator.desktop ~/.local/share/applications/
```

Now open **Kickoff** (application launcher) and search for **"N1 Translator"**.
Click to launch.

> **Tip:** You can also right-click the app launcher entry and select **"Add to Panel"** or **"Add to Desktop"** for one-click access.

---

## 5. Application Icon

The icon (`assets/n1-translator.png`) is already referenced in the `.desktop` file.
KDE will pick it up automatically once the desktop file is installed.

If the icon doesn't appear after copying the `.desktop` file, refresh the system cache:

```bash
kbuildsycoca6
```

---

## 6. Auto-Start with KDE

To have N1 Translator start automatically when you log in:

```bash
# Create a symlink in KDE's autostart folder
ln -s ~/.local/share/applications/n1-translator.desktop ~/.config/autostart/
```

Or via **System Settings**:
1. Open **System Settings** → **Startup and Shutdown** → **Autostart**
2. Click **Add Application** → select **N1 Translator** from the list

---

## 7. Usage

| Action | Result |
|---|---|
| Copy Japanese text | Translates to Spanish (JP → ES) |
| Copy Spanish text (with accents/ñ) | Translates to Japanese (ES → JP) |
| Click **top bar** of overlay (green dot / status) | Opens quick menu (Settings, Test, Pause, Exit) |
| Click **translation text** | Copies translation to clipboard |
| **Left-click** tray icon | Show / hide the overlay |
| Search "N1 Translator" in Kickoff | Launch the app |

### Quick Menu (click overlay top bar)

| Item | Action |
|---|---|
| ⚙ Settings | Configure accent, background, fonts, pet GIF, window width |
| 🧪 Test | Alternates JP→ES / ES→JP each click |
| 🔛 Pause / Resume | Toggle clipboard monitoring |
| ✕ Exit | Quit the application |

---

## 8. Configuration Reference

| Setting | Default | Description |
|---|---|---|
| **Accent colour** | `#22c55e` (green) | 7 presets + custom colour picker (🎨) |
| **Background colour** | `#08080e` (carbon) | 7 presets + custom colour picker (🎨) |
| **Background opacity** | 215 | Slider from 30 (barely visible) to 255 (fully opaque) |
| **Japanese font** | Noto Sans CJK JP | Any installed font |
| **Japanese font size** | 11 pt | 8–32 range |
| **Spanish font** | sans-serif | Any installed font |
| **Spanish font size** | 13 pt | 8–32 range |
| **Custom window width** | Off (420 px) | Override the default width (280–1200 px) |
| **Pet GIF** | Off | Animated GIF on the right side; paste any `https://…giphy.gif` URL |

---

## 9. Project Structure

```
n1-translator/
├── pyproject.toml              # Build metadata & CLI entry point
├── INSTALL.md                  # This file
├── README.md                   # Project overview
├── LICENSE                     # MIT
├── requirements.txt            # pip dependencies
├── assets/
│   ├── n1-translator.desktop   # KDE application launcher
│   └── n1-translator.png       # 64×64 app icon (purple)
├── scripts/
│   └── start.sh                # Production launcher (auto-setup, detached)
├── start.sh                    # Legacy — delegates to scripts/
└── src/
    └── n1_translator/
        ├── __init__.py
        ├── __main__.py          # CLI entry: ``python -m n1_translator``
        ├── app.py               # Application class, tray, clipboard polling
        ├── overlay.py           # Translucent overlay widget & animations
        └── settings.py          # QSettings persistence & settings dialog
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No translation appears | `wl-paste` not installed | `sudo pacman -S wl-clipboard` |
| Overlay looks solid (no blur) | Compositor blur not supported | Works on KDE Plasma Wayland out of the box |
| Translation errors | Google Translate rate limit | Wait a few seconds and retry; repeated text uses cache |
| App doesn't start from Kickoff | Desktop file path is stale | Update `Exec=` line in `~/.local/share/applications/n1-translator.desktop` |
| Icon missing in app launcher | Cache not refreshed | Run `kbuildsycoca6` |
