# Takoyomi — Installation Guide

Step-by-step instructions to install Takoyomi on **KDE Plasma (Wayland)**.

---

## Prerequisites

- **Arch Linux** (other distros work too, but paths may vary)
- **KDE Plasma** on **Wayland**
- **wl-clipboard** — provides `wl-paste` for clipboard monitoring
- **Python** ≥ 3.12

```bash
# Arch Linux
sudo pacman -S wl-clipboard python python-pip git
```

---

## AUR Installation (Arch Linux)

```bash
yay -S takoyomi
```

---

## Manual Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kurojs/takoyomi.git
cd takoyomi
```

### 2. Virtual Environment & Dependencies

The project ships with `scripts/start.sh` which handles everything automatically.

```bash
./start.sh
```

Or manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3. Quick Test

```bash
python -m takoyomi
```

You should see a translucent overlay appear in the bottom-right corner. Copy some Japanese text — the overlay will show the translation.

### 4. KDE Application Launcher

```bash
cp assets/takoyomi.desktop ~/.local/share/applications/
```

Search for **"Takoyomi"** in Kickoff.

### 5. Auto-Start with KDE

```bash
ln -s ~/.local/share/applications/takoyomi.desktop ~/.config/autostart/
```

---

## Configuration

Settings are persisted via QSettings (`~/.config/takoyomi-tools/Takoyomi.conf`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No translation appears | `wl-paste` not installed | `sudo pacman -S wl-clipboard` |
| Overlay looks solid (no blur) | Compositor blur not supported | Works on KDE Plasma Wayland out of the box |
| Translation errors | Google Translate rate limit | Wait a few seconds and retry; repeated text uses cache |
