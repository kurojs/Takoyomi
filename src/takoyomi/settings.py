from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QFormLayout,
    QDialogButtonBox, QFontComboBox, QWidget, QFrame,
    QCheckBox, QLineEdit, QColorDialog, QSlider,
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter

from takoyomi.i18n import (
    get as _,
    TARGET_LANGUAGES,
    UI_LANGUAGES,
    target_lang_name,
)

ACCENT_COLORS = {
    "Verde":    "#22c55e",
    "Azul":     "#3b82f6",
    "Púrpura":  "#a855f7",
    "Naranja":  "#f97316",
    "Rojo":     "#ef4444",
    "Teal":     "#14b8a6",
    "Rosa":     "#ec4899",
}

_ACCENT_LIST = list(ACCENT_COLORS.items())

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
    "accent":            "#22c55e",
    "bg_color":          "#08080e",
    "bg_opacity":        215,
    "jp_font":           "Noto Sans CJK JP",
    "jp_size":           11,
    "es_font":           "sans-serif",
    "es_size":           13,
    "width":             420,
    "width_custom":      False,
    "pet_enabled":       False,
    "pet_url":           "",
    "ui_language":       "en",
    "target_language":   "es",
}


class AppSettings:
    def __init__(self):
        self._qs = QSettings("takoyomi-tools", "Takoyomi")
        self.load()

    def load(self):
        for k, v in DEFAULTS.items():
            typed = self._qs.value(k, v, type=type(v))
            setattr(self, k, typed)
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


class _ColorSwatch(QLabel):
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


class SettingsDialog(QDialog):
    applied = Signal()

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._dirty = False
        self._lang = settings.ui_language

        self.setWindowTitle(_("settings_title", self._lang))
        self.setMinimumWidth(380)

        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        lang = self._lang

        accent_row = QHBoxLayout()
        self._accent_combo = QComboBox()
        for name, hex_c in _ACCENT_LIST:
            self._accent_combo.addItem(f" ● {name}", hex_c)
        accent_row.addWidget(self._accent_combo, 1)

        self._custom_btn = QPushButton("🎨")
        self._custom_btn.setFixedWidth(36)
        self._custom_btn.setToolTip(_("custom_color", lang))
        self._custom_btn.clicked.connect(self._pick_custom)
        accent_row.addWidget(self._custom_btn)
        layout.addLayout(accent_row)

        self._jp_font_combo = QFontComboBox()
        self._jp_font_combo.setFontFilters(QFontComboBox.FontFilter.AllFonts)
        self._jp_size_spin = QSpinBox()
        self._jp_size_spin.setRange(8, 32)
        layout.addLayout(self._labeled(_("jp_font", lang), self._jp_font_combo))

        fs_jp = QHBoxLayout()
        fs_jp.addWidget(QLabel(f"{_('jp_size', lang)}:"))
        fs_jp.addWidget(self._jp_size_spin)
        fs_jp.addStretch()
        layout.addLayout(fs_jp)

        self._es_font_combo = QFontComboBox()
        self._es_font_combo.setFontFilters(QFontComboBox.FontFilter.AllFonts)
        self._es_size_spin = QSpinBox()
        self._es_size_spin.setRange(8, 32)
        layout.addLayout(self._labeled(_("trans_font", lang), self._es_font_combo))

        fs_es = QHBoxLayout()
        fs_es.addWidget(QLabel(f"{_('trans_size', lang)}:"))
        fs_es.addWidget(self._es_size_spin)
        fs_es.addStretch()
        layout.addLayout(fs_es)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,30);")
        layout.addWidget(sep)

        lang_row = QHBoxLayout()
        self._ui_lang_combo = QComboBox()
        for code, name in UI_LANGUAGES:
            self._ui_lang_combo.addItem(name, code)
        lang_row.addWidget(QLabel(f"{_('ui_lang', lang)}:"))
        lang_row.addWidget(self._ui_lang_combo, 1)
        layout.addLayout(lang_row)

        tgt_row = QHBoxLayout()
        self._target_lang_combo = QComboBox()
        for code, name in TARGET_LANGUAGES:
            self._target_lang_combo.addItem(name, code)
        tgt_row.addWidget(QLabel(f"{_('target_lang', lang)}:"))
        tgt_row.addWidget(self._target_lang_combo, 1)
        layout.addLayout(tgt_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: rgba(255,255,255,30);")
        layout.addWidget(sep2)

        self._pet_check = QCheckBox(_("pet_check", lang))
        self._pet_check.toggled.connect(self._on_pet_toggled)
        layout.addWidget(self._pet_check)

        pet_url_row = QHBoxLayout()
        self._pet_url_input = QLineEdit()
        self._pet_url_input.setPlaceholderText(_("pet_placeholder", lang))
        self._pet_url_input.setEnabled(False)
        pet_url_row.addWidget(QLabel(f"{_('url', lang)}:"))
        pet_url_row.addWidget(self._pet_url_input, 1)
        layout.addLayout(pet_url_row)

        width_row = QHBoxLayout()
        self._width_check = QCheckBox(_("custom_width", lang))
        self._width_check.toggled.connect(self._on_width_toggled)
        width_row.addWidget(self._width_check)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(280, 1200)
        self._width_spin.setSuffix(_("px", lang))
        self._width_spin.setEnabled(False)
        width_row.addWidget(self._width_spin)
        width_row.addStretch()
        layout.addLayout(width_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color: rgba(255,255,255,30);")
        layout.addWidget(sep3)

        bg_row = QHBoxLayout()
        self._bg_combo = QComboBox()
        for name, hex_c in _BG_LIST:
            self._bg_combo.addItem(f" ● {name}", hex_c)
        bg_row.addWidget(self._bg_combo, 1)

        self._bg_custom_btn = QPushButton("🎨")
        self._bg_custom_btn.setFixedWidth(36)
        self._bg_custom_btn.setToolTip(_("custom_color", lang))
        self._bg_custom_btn.clicked.connect(self._pick_bg_custom)
        bg_row.addWidget(self._bg_custom_btn)
        layout.addLayout(bg_row)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel(f"{_('opacity', lang)}:"))
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

        btn_row = QHBoxLayout()
        reset_btn = QPushButton(f"↺ {_('reset', lang)}")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton(_("cancel", lang))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        apply_btn = QPushButton(_("apply", lang))
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

    def _load(self):
        s = self._settings
        lang = s.ui_language

        idx = self._accent_combo.findData(s.accent)
        if idx >= 0:
            self._accent_combo.setCurrentIndex(idx)
        else:
            self._accent_combo.addItem(f" ● Custom ({s.accent})", s.accent)
            self._accent_combo.setCurrentIndex(self._accent_combo.count() - 1)

        self._jp_font_combo.setCurrentFont(QFont(s.jp_font))
        self._jp_size_spin.setValue(s.jp_size)
        self._es_font_combo.setCurrentFont(QFont(s.es_font))
        self._es_size_spin.setValue(s.es_size)

        uid = self._ui_lang_combo.findData(s.ui_language)
        if uid >= 0:
            self._ui_lang_combo.setCurrentIndex(uid)
        tgt = self._target_lang_combo.findData(s.target_language)
        if tgt >= 0:
            self._target_lang_combo.setCurrentIndex(tgt)
        else:
            self._target_lang_combo.addItem(target_lang_name(s.target_language), s.target_language)
            self._target_lang_combo.setCurrentIndex(self._target_lang_combo.count() - 1)

        self._width_check.setChecked(s.width_custom)
        self._width_spin.setValue(s.width)
        self._width_spin.setEnabled(s.width_custom)

        self._pet_check.setChecked(s.pet_enabled)
        self._pet_url_input.setText(s.pet_url)
        self._pet_url_input.setEnabled(s.pet_enabled)

        bidx = self._bg_combo.findData(s.bg_color)
        if bidx >= 0:
            self._bg_combo.setCurrentIndex(bidx)
        else:
            self._bg_combo.addItem(f" ● Custom ({s.bg_color})", s.bg_color)
            self._bg_combo.setCurrentIndex(self._bg_combo.count() - 1)
        self._bg_opacity_slider.setValue(s.bg_opacity)
        self._bg_opacity_label.setText(str(s.bg_opacity))

    def _pick_custom(self):
        current = self._accent_combo.currentData() or "#22c55e"
        color = QColorDialog.getColor(
            QColor(current), self, _("accent_picker", self._lang),
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
        current = self._bg_combo.currentData() or "#08080e"
        color = QColorDialog.getColor(
            QColor(current), self, _("bg_picker", self._lang),
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
        s.ui_language = self._ui_lang_combo.currentData()
        s.target_language = self._target_lang_combo.currentData()
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
