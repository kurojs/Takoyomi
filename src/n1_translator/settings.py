"""
settings.py — Configuración persistente y diálogo de ajustes.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QFormLayout,
    QDialogButtonBox, QFontComboBox, QWidget, QFrame,
    QCheckBox, QLineEdit, QColorDialog, QSlider,
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter


# ── Paleta de acentos ───────────────────────

ACCENT_COLORS = {
    "Verde":    "#22c55e",
    "Azul":     "#3b82f6",
    "Púrpura":  "#a855f7",
    "Naranja":  "#f97316",
    "Rojo":     "#ef4444",
    "Teal":     "#14b8a6",
    "Rosa":     "#ec4899",
}

_ACCENT_LIST = list(ACCENT_COLORS.items())  # [(nombre, hex), ...]

BG_COLORS = {
    "Carbon":       "#08080e",
    "Black":        "#000000",
    "Dark Gray":    "#0a0a0a",
    "Navy":         "#1a1a2e",
    "GitHub Dark":  "#0d1117",
    "Catppuccin":   "#1e1e2e",
    "Obsidian":     "#1b1b2f",
}

_BG_LIST = list(BG_COLORS.items())

DEFAULTS = {
    "accent":       "#22c55e",
    "bg_color":     "#08080e",
    "bg_opacity":   215,
    "jp_font":      "Noto Sans CJK JP",
    "jp_size":      11,
    "es_font":      "sans-serif",
    "es_size":      13,
    "width":        420,
    "width_custom": False,
    "pet_enabled":  False,
    "pet_url":      "",
}


# ── AppSettings (QSettings) ─────────────────

class AppSettings:
    """Persistencia vía QSettings."""

    def __init__(self):
        self._qs = QSettings("n1-tools", "N1 Translator")
        self.load()

    def load(self):
        for k, v in DEFAULTS.items():
            typed = self._qs.value(k, v, type=type(v))
            setattr(self, k, typed)
        # Ensure numeric types (QSettings may return int/str depending on backend)
        self.jp_size    = int(self.jp_size)
        self.es_size    = int(self.es_size)
        self.width      = int(self.width)
        self.bg_opacity = int(self.bg_opacity)
        self.pet_enabled   = bool(self.pet_enabled)
        self.width_custom  = bool(self.width_custom)

    def save(self):
        for k in DEFAULTS:
            self._qs.setValue(k, getattr(self, k))

    def reset(self):
        for k, v in DEFAULTS.items():
            setattr(self, k, v)

    def accent_qcolor(self) -> QColor:
        return QColor(self.accent)

    def bg_qcolor(self) -> QColor:
        c = QColor(self.bg_color)
        c.setAlpha(self.bg_opacity)
        return c


# ── Previsualización de color ───────────────

class _ColorSwatch(QLabel):
    """Cuadradito de 16×16 con el color."""
    def __init__(self, hex_color: str):
        super().__init__()
        self.setFixedSize(16, 16)
        self._hex = hex_color
        self._render()

    def _render(self):
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(self._hex))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 16, 16, 3, 3)
        p.end()
        self.setPixmap(pm)


# ── Diálogo de ajustes ─────────────────────

class SettingsDialog(QDialog):
    """Ventana de configuración visual."""

    applied = Signal()  # se emite cuando se aplican cambios

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._dirty = False

        self.setWindowTitle("Ajustes — N1 Translator")
        self.setMinimumWidth(380)

        self._build_ui()
        self._load()

    # ── Construcción ─────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # --- Acento ---
        accent_row = QHBoxLayout()
        self._accent_combo = QComboBox()
        for name, hex_c in _ACCENT_LIST:
            self._accent_combo.addItem(f" ● {name}", hex_c)
        accent_row.addWidget(self._accent_combo, 1)

        self._custom_btn = QPushButton("🎨")
        self._custom_btn.setFixedWidth(36)
        self._custom_btn.setToolTip("Elegir color personalizado…")
        self._custom_btn.clicked.connect(self._pick_custom)
        accent_row.addWidget(self._custom_btn)
        layout.addLayout(accent_row)

        # --- Fuentes ---
        self._jp_font_combo = QFontComboBox()
        self._jp_font_combo.setFontFilters(QFontComboBox.FontFilter.MonospacedFonts)
        # Queremos TODAS las fuentes, no solo mono
        self._jp_font_combo.setFontFilters(QFontComboBox.FontFilter.AllFonts)
        self._jp_size_spin = QSpinBox()
        self._jp_size_spin.setRange(8, 32)
        layout.addLayout(self._labeled("Fuente japonés:",  self._jp_font_combo))

        fs_jp = QHBoxLayout()
        fs_jp.addWidget(QLabel("Tamaño JP:"))
        fs_jp.addWidget(self._jp_size_spin)
        fs_jp.addStretch()
        layout.addLayout(fs_jp)

        self._es_font_combo = QFontComboBox()
        self._es_font_combo.setFontFilters(QFontComboBox.FontFilter.AllFonts)
        self._es_size_spin = QSpinBox()
        self._es_size_spin.setRange(8, 32)
        layout.addLayout(self._labeled("Fuente español:", self._es_font_combo))

        fs_es = QHBoxLayout()
        fs_es.addWidget(QLabel("Tamaño ES:"))
        fs_es.addWidget(self._es_size_spin)
        fs_es.addStretch()
        layout.addLayout(fs_es)

        # ── Separador ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,30);")
        layout.addWidget(sep)

        # ── Pet ──
        self._pet_check = QCheckBox("🐾 Pet — mostrar GIF animado al costado")
        self._pet_check.toggled.connect(self._on_pet_toggled)
        layout.addWidget(self._pet_check)

        pet_url_row = QHBoxLayout()
        self._pet_url_input = QLineEdit()
        self._pet_url_input.setPlaceholderText("https://media1.giphy.com/media/…/giphy.gif")
        self._pet_url_input.setEnabled(False)
        pet_url_row.addWidget(QLabel("URL:"))
        pet_url_row.addWidget(self._pet_url_input, 1)
        layout.addLayout(pet_url_row)

        # ── Ancho de ventana ──
        width_row = QHBoxLayout()
        self._width_check = QCheckBox("✎ Custom window width")
        self._width_check.toggled.connect(self._on_width_toggled)
        width_row.addWidget(self._width_check)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(280, 1200)
        self._width_spin.setSuffix(" px")
        self._width_spin.setEnabled(False)
        width_row.addWidget(self._width_spin)
        width_row.addStretch()
        layout.addLayout(width_row)

        # ── Separador ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: rgba(255,255,255,30);")
        layout.addWidget(sep2)

        # ── Fondo ──
        bg_row = QHBoxLayout()
        self._bg_combo = QComboBox()
        for name, hex_c in _BG_LIST:
            self._bg_combo.addItem(f" ● {name}", hex_c)
        bg_row.addWidget(self._bg_combo, 1)

        self._bg_custom_btn = QPushButton("🎨")
        self._bg_custom_btn.setFixedWidth(36)
        self._bg_custom_btn.setToolTip("Elegir color de fondo…")
        self._bg_custom_btn.clicked.connect(self._pick_bg_custom)
        bg_row.addWidget(self._bg_custom_btn)
        layout.addLayout(bg_row)

        # Opacidad del fondo
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Opacidad:"))
        self._bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._bg_opacity_slider.setRange(30, 255)
        self._bg_opacity_slider.setValue(215)
        op_row.addWidget(self._bg_opacity_slider, 1)

        self._bg_opacity_label = QLabel("215")
        self._bg_opacity_label.setFixedWidth(28)
        self._bg_opacity_slider.valueChanged.connect(
            lambda v: self._bg_opacity_label.setText(str(v))
        )
        op_row.addWidget(self._bg_opacity_label)
        layout.addLayout(op_row)

        layout.addStretch()

        # --- Botones ---
        btn_row = QHBoxLayout()

        reset_btn = QPushButton("↺ Restaurar defaults")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        apply_btn = QPushButton("Aplicar")
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(apply_btn)

        layout.addLayout(btn_row)

    @staticmethod
    def _labeled(text: str, widget: QWidget) -> QHBoxLayout:
        lb = QHBoxLayout()
        lb.addWidget(QLabel(text))
        lb.addWidget(widget)
        return lb

    # ── Cargar / Guardar ─────────────────────

    def _load(self):
        s = self._settings

        # Acento: buscar en presets, si no está agregar custom
        idx = self._accent_combo.findData(s.accent)
        if idx >= 0:
            self._accent_combo.setCurrentIndex(idx)
        else:
            self._accent_combo.addItem(f" ● Custom ({s.accent})", s.accent)
            self._accent_combo.setCurrentIndex(self._accent_combo.count() - 1)

        # QFontComboBox necesita un nombre de familia exacto
        self._jp_font_combo.setCurrentFont(QFont(s.jp_font))
        self._jp_size_spin.setValue(s.jp_size)
        self._es_font_combo.setCurrentFont(QFont(s.es_font))
        self._es_size_spin.setValue(s.es_size)

        # Ancho
        self._width_check.setChecked(s.width_custom)
        self._width_spin.setValue(s.width)
        self._width_spin.setEnabled(s.width_custom)

        # Pet
        self._pet_check.setChecked(s.pet_enabled)
        self._pet_url_input.setText(s.pet_url)
        self._pet_url_input.setEnabled(s.pet_enabled)

        # Fondo
        bidx = self._bg_combo.findData(s.bg_color)
        if bidx >= 0:
            self._bg_combo.setCurrentIndex(bidx)
        else:
            self._bg_combo.addItem(f" ● Custom ({s.bg_color})", s.bg_color)
            self._bg_combo.setCurrentIndex(self._bg_combo.count() - 1)
        self._bg_opacity_slider.setValue(s.bg_opacity)
        self._bg_opacity_label.setText(str(s.bg_opacity))

    def _pick_custom(self):
        """Selector de color personalizado vía QColorDialog."""
        current = self._accent_combo.currentData() or "#22c55e"
        color = QColorDialog.getColor(
            QColor(current), self, "Elegir color de acento",
        )
        if not color.isValid():
            return
        hex_c = color.name()
        idx = self._accent_combo.findData(hex_c)
        if idx >= 0:
            self._accent_combo.setCurrentIndex(idx)
        else:
            self._accent_combo.addItem(f" ● Custom ({hex_c})", hex_c)
            self._accent_combo.setCurrentIndex(self._accent_combo.count() - 1)

    def _pick_bg_custom(self):
        """Selector de color de fondo personalizado."""
        current = self._bg_combo.currentData() or "#08080e"
        color = QColorDialog.getColor(
            QColor(current), self, "Elegir color de fondo",
        )
        if not color.isValid():
            return
        hex_c = color.name()
        idx = self._bg_combo.findData(hex_c)
        if idx >= 0:
            self._bg_combo.setCurrentIndex(idx)
        else:
            self._bg_combo.addItem(f" ● Custom ({hex_c})", hex_c)
            self._bg_combo.setCurrentIndex(self._bg_combo.count() - 1)

    def _on_pet_toggled(self, checked: bool):
        self._pet_url_input.setEnabled(checked)

    def _on_width_toggled(self, checked: bool):
        self._width_spin.setEnabled(checked)

    def _apply(self):
        s = self._settings
        s.accent = self._accent_combo.currentData()
        s.bg_color = self._bg_combo.currentData()
        s.bg_opacity = self._bg_opacity_slider.value()
        s.jp_font = self._jp_font_combo.currentFont().family()
        s.jp_size = self._jp_size_spin.value()
        s.es_font = self._es_font_combo.currentFont().family()
        s.es_size = self._es_size_spin.value()
        s.width_custom = self._width_check.isChecked()
        if s.width_custom:
            s.width = self._width_spin.value()
        s.pet_enabled = self._pet_check.isChecked()
        s.pet_url = self._pet_url_input.text().strip()
        s.save()
        self._dirty = True
        self.applied.emit()
        self.accept()

    def _reset(self):
        self._settings.reset()
        self._load()

    @property
    def was_applied(self) -> bool:
        return self._dirty
