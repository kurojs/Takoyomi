from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QApplication,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, Property, QRectF, Signal, QUrl,
)
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient, QMovie,
)
from PySide6.QtWidgets import QMenu
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from takoyomi.settings import AppSettings
from takoyomi.i18n import get as _


class LoadingLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self._progress = 0.0
        self._active = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._accent = QColor(34, 197, 94)
        self._timer.start(16)

    def set_accent(self, color: QColor):
        self._accent = color
        self.update()

    def start_loading(self):
        self._active = True
        self._progress = 0.0
        self.show()

    def stop_loading(self):
        self._active = False
        self._progress = 0.0
        self.update()

    def _tick(self):
        self._progress += 0.025
        if self._progress > 1.0:
            self._progress = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        p = self._progress
        a = self._accent
        if self._active:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0,                QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(max(0.0, p - 0.08), QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(p,                  QColor(a.red(), a.green(), a.blue(), 220))
            grad.setColorAt(min(1.0, p + 0.08), QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(1.0,                QColor(a.red(), a.green(), a.blue(), 25))
        else:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0,                QColor(a.red(), a.green(), a.blue(), 55))
            grad.setColorAt(max(0.0, p - 0.04), QColor(a.red(), a.green(), a.blue(), 55))
            grad.setColorAt(p,                  QColor(a.red(), a.green(), a.blue(), 190))
            grad.setColorAt(min(1.0, p + 0.04), QColor(a.red(), a.green(), a.blue(), 55))
            grad.setColorAt(1.0,                QColor(a.red(), a.green(), a.blue(), 55))
        painter.fillRect(self.rect(), grad)


class TranslatorPopup(QWidget):
    settings_requested = Signal()
    test_requested = Signal()
    toggle_requested = Signal()
    quit_requested = Signal()

    def __init__(self):
        super().__init__(None)
        self._pulse = 1.0
        self._settings = AppSettings()
        self._acc = self._settings.accent_qcolor()
        self._lang = self._settings.ui_language

        self._pet_movie = None
        self._pet_path = ""
        self._last_pet_url = ""
        self._bg_color = QColor(8, 8, 14)
        self._bg_opacity = 215

        self._setup_window()
        self._setup_ui()
        self._setup_animations()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMinimumHeight(60)

    def _setup_ui(self):
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(22, 16, 22, 16)
        self._outer.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.indicator = QLabel("●")
        self.indicator.setFixedWidth(12)
        top.addWidget(self.indicator)
        self.status_label = QLabel(f"　{_('status_idle', self._lang)}")
        self.status_label.setStyleSheet("font-size: 11px; background: transparent;")
        top.addWidget(self.status_label)
        top.addStretch()
        self._outer.addLayout(top)

        self.jp_label = QLabel("　")
        self.jp_label.setWordWrap(True)
        self.jp_label.setMinimumHeight(18)
        self._outer.addWidget(self.jp_label)

        self.loading_line = LoadingLine()
        self._outer.addWidget(self.loading_line)

        self.es_label = QLabel("　")
        self.es_label.setWordWrap(True)
        self.es_label.setMinimumHeight(18)
        self._outer.addWidget(self.es_label)

        self._pet_label = QLabel(self)
        self._pet_label.setFixedSize(80, 80)
        self._pet_label.setScaledContents(True)
        self._pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pet_label.hide()

        self._apply_settings_to_ui()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_pet()

    def _reposition_pet(self):
        if not self._pet_label.isVisible():
            return
        cr = self.contentsRect()
        x = cr.right() - 80 - 22
        y = max(50, (self.height() - 80) // 2)
        self._pet_label.move(x, y)

    def _apply_settings_to_ui(self):
        s = self._settings
        a = self._acc
        self._lang = s.ui_language

        self.setFixedWidth(s.width)
        right_margin = 22 + (100 if s.pet_enabled and s.pet_url else 0)
        self._outer.setContentsMargins(22, 16, right_margin, 16)

        self.indicator.setStyleSheet(f"color: {s.accent}; font-size: 10px;")
        self.status_label.setStyleSheet(
            "color: rgba(255,255,255,100); font-size: 11px; background: transparent;"
        )

        jp_f = QFont(s.jp_font, s.jp_size)
        jp_f.setWeight(QFont.Weight.Light)
        self.jp_label.setFont(jp_f)
        self.jp_label.setStyleSheet(
            "color: rgba(255,255,255,140); background: transparent;"
        )

        es_f = QFont(s.es_font, s.es_size)
        self.es_label.setFont(es_f)
        self.es_label.setStyleSheet("color: white; background: transparent;")

        self.loading_line.set_accent(a)

        self._bg_color = QColor(s.bg_color)
        self._bg_opacity = int(s.bg_opacity)

        if s.pet_enabled and s.pet_url:
            self._pet_label.show()
            self._reposition_pet()
            if s.pet_url != getattr(self, "_last_pet_url", ""):
                self._download_pet_gif(s.pet_url)
                self._last_pet_url = s.pet_url
        else:
            self._pet_label.hide()
            if self._pet_movie:
                self._pet_movie.stop()
                self._pet_movie = None

        self.update()

    def _download_pet_gif(self, url: str):
        self._net = QNetworkAccessManager()
        req = QNetworkRequest(QUrl(url))
        reply = self._net.get(req)
        reply.finished.connect(lambda r=reply: self._on_pet_loaded(r))

    def _on_pet_loaded(self, reply):
        data = reply.readAll()
        if not data or data.isEmpty():
            return
        self._pet_path = f"/tmp/takoyomi_pet_{id(self)}.gif"
        with open(self._pet_path, "wb") as f:
            f.write(bytes(data))
        if self._pet_movie:
            self._pet_movie.stop()
        self._pet_movie = QMovie(self._pet_path)
        self._pet_movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._pet_movie.setScaledSize(self._pet_label.size())
        self._pet_label.setMovie(self._pet_movie)
        self._pet_movie.start()
        self._reposition_pet()

    def _setup_animations(self):
        self._pulse_anim = QPropertyAnimation(self, b"pulse_val")
        self._pulse_anim.setDuration(1600)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setKeyValueAt(0.0, 0.35)
        self._pulse_anim.setKeyValueAt(0.5, 1.0)
        self._pulse_anim.setKeyValueAt(1.0, 0.35)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), 14, 14)
        bg = QColor(self._bg_color)
        bg.setAlpha(self._bg_opacity)
        painter.setBrush(bg)
        a = self._acc
        painter.setPen(QPen(QColor(a.red(), a.green(), a.blue(), 35), 1))
        painter.drawPath(path)

    def update_settings(self, s: AppSettings):
        self._settings = s
        self._acc = s.accent_qcolor()
        self._lang = s.ui_language
        self._apply_settings_to_ui()
        self.move_to_position()

    def show_translation(self, src_text: str, tgt_text: str):
        self.jp_label.setText(src_text.strip())
        self.es_label.setText(tgt_text.strip())
        self.es_label.setStyleSheet("color: white; background: transparent;")
        self.status_label.setText(f"　{_('status_done', self._lang)}")
        self.loading_line.stop_loading()
        self._restart_pulse()
        self._resize_to_content()

    def show_translating(self):
        self.status_label.setText(f"　{_('status_translating', self._lang)}")
        self.loading_line.start_loading()

    def show_error(self, msg: str):
        self.es_label.setText(f"⚠ {msg}")
        self.es_label.setStyleSheet("color: #ef4444; background: transparent;")
        self.status_label.setText(f"　{_('status_error', self._lang)}")
        self.status_label.setStyleSheet("color: rgba(239,68,68,150); font-size: 11px; background: transparent;")
        self.loading_line.stop_loading()
        self._restart_pulse()
        self._resize_to_content()

    def show_idle(self):
        self.jp_label.setText("　")
        self.es_label.setText("　")
        self.status_label.setText(f"　{_('status_idle', self._lang)}")
        self.loading_line.stop_loading()
        self._resize_to_content()

    def _resize_to_content(self):
        margins = self._outer.contentsMargins()
        spacing = self._outer.spacing()
        avail_w = self.width() - margins.left() - margins.right()
        jp_h = self.jp_label.heightForWidth(avail_w)
        es_h = self.es_label.heightForWidth(avail_w)
        h = (margins.top()
             + self._outer.itemAt(0).sizeHint().height()
             + spacing
             + max(jp_h, 18)
             + spacing
             + 2
             + spacing
             + max(es_h, 18)
             + margins.bottom())
        screen = QApplication.primaryScreen()
        if screen:
            h = min(h, screen.availableGeometry().height() - 40)
        self.setFixedHeight(max(60, h))
        self.move_to_position()

    def move_to_position(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 20
        y = geo.bottom() - self.height() - 20
        self.move(x, y)

    def show_overlay(self):
        self.move_to_position()
        self.setWindowOpacity(1.0)
        if not self.isVisible():
            self.show()
            self.raise_()

    def hide_overlay(self):
        self.hide()

    def mousePressEvent(self, event):
        if event.position().y() < 28:
            self._show_quick_menu(event)
            return
        es = self.es_label.text()
        if es and "⚠" not in es and es.strip() and es != "　":
            cb = QApplication.clipboard()
            cb.setText(es)

    def _show_quick_menu(self, event):
        menu = QMenu(self)
        lang = self._lang

        act_settings = menu.addAction(f"⚙ {_('menu_settings', lang)}")
        act_settings.triggered.connect(self.settings_requested.emit)

        act_test = menu.addAction(f"🧪 {_('menu_test', lang)}")
        act_test.triggered.connect(self.test_requested.emit)

        menu.addSeparator()

        act_toggle = menu.addAction(f"🔛 {_('menu_toggle', lang)}")
        act_toggle.triggered.connect(self.toggle_requested.emit)

        menu.addSeparator()

        act_quit = menu.addAction(f"✕ {_('menu_quit', lang)}")
        act_quit.triggered.connect(self.quit_requested.emit)

        menu.exec(event.globalPosition().toPoint())

    def _restart_pulse(self):
        self._pulse_anim.stop()
        self._pulse_anim.start()

    def set_pulse_val(self, val: float):
        self._pulse = val
        a = self._acc
        self.indicator.setStyleSheet(
            f"color: rgba({a.red()},{a.green()},{a.blue()},{val:.2f}); font-size: 10px;"
        )

    def get_pulse_val(self):
        return self._pulse

    pulse_val = Property(float, get_pulse_val, set_pulse_val)
