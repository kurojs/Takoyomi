"""
popup.py — Overlay transparente SIEMPRE visible.
Colores, fuentes y tamaños configurables vía AppSettings.
"""

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

from settings import AppSettings

# ── ¿Soporta windowOpacity? ─────────────────

_CAN_FADE: bool = False
try:
    from PySide6.QtX11Extras import QX11Info
    _CAN_FADE = QX11Info.isPlatformX11()
except ImportError:
    pass


# ─────────────────────────────────────────────
#  LOADING LINE
# ─────────────────────────────────────────────

class LoadingLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self._progress = 0.0
        self._active = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._accent = QColor(34, 197, 94)

    def set_accent(self, color: QColor):
        self._accent = color
        if not self._active:
            self.update()

    def start_loading(self):
        self._active = True
        self._progress = 0.0
        self._timer.start(16)
        self.show()

    def stop_loading(self):
        self._active = False
        self._timer.stop()
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

        if self._active:
            grad = QLinearGradient(0, 0, w, 0)
            p = self._progress
            a = self._accent
            grad.setColorAt(0.0,                  QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(max(0.0, p - 0.08),   QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(p,                    QColor(a.red(), a.green(), a.blue(), 220))
            grad.setColorAt(min(1.0, p + 0.08),   QColor(a.red(), a.green(), a.blue(), 25))
            grad.setColorAt(1.0,                  QColor(a.red(), a.green(), a.blue(), 25))
            painter.fillRect(self.rect(), grad)
        else:
            a = self._accent
            painter.fillRect(self.rect(), QColor(a.red(), a.green(), a.blue(), 45))


# ─────────────────────────────────────────────
#  OVERLAY PRINCIPAL
# ─────────────────────────────────────────────

class TranslatorPopup(QWidget):
    """
    Overlay frameless, semi-transparente, siempre al frente.
    Colores y fuentes configurables desde AppSettings.
    """

    # Señales para el menú rápido (click en barra superior)
    settings_requested = Signal()
    test_requested = Signal()
    toggle_requested = Signal()
    quit_requested = Signal()

    def __init__(self):
        super().__init__(None)
        self._pulse = 1.0
        self._settings = AppSettings()
        self._acc = self._settings.accent_qcolor()

        self._pet_movie = None
        self._pet_path = ""
        self._last_pet_url = ""

        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        self._setup_blur()

    # ── Ventana ───────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMinimumHeight(60)
        self.setMaximumHeight(600)

    # ── UI ────────────────────────────────────

    def _setup_ui(self):
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(22, 16, 22, 16)
        self._outer.setSpacing(8)

        # ── Fila superior ──
        top = QHBoxLayout()
        top.setSpacing(8)

        self.indicator = QLabel("●")
        self.indicator.setFixedWidth(12)
        top.addWidget(self.indicator)

        self.status_label = QLabel("　En espera…")
        self.status_label.setStyleSheet("font-size: 11px; background: transparent;")
        top.addWidget(self.status_label)
        top.addStretch()
        self._outer.addLayout(top)

        # ── Texto japonés ──
        self.jp_label = QLabel("　")
        self.jp_label.setWordWrap(True)
        self.jp_label.setMinimumHeight(18)
        self._outer.addWidget(self.jp_label)

        # ── Línea animada ──
        self.loading_line = LoadingLine()
        self._outer.addWidget(self.loading_line)

        # ── Traducción ──
        self.es_label = QLabel("　")
        self.es_label.setWordWrap(True)
        self.es_label.setMinimumHeight(18)
        self._outer.addWidget(self.es_label)

        # ── Pet (posicionado absolutamente sobre el widget) ──
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
        """Coloca el pet_label en la esquina derecha del contenido."""
        if self._pet_label.isVisible():
            x = self.width() - 22 - 80  # 22px margen derecho + 80px pet
            y = max(50, (self.height() - 80) // 2)
            self._pet_label.move(x, y)

    def _apply_settings_to_ui(self):
        """Refleja el AppSettings actual en los widgets."""
        s = self._settings
        a = self._acc

        self.setFixedWidth(s.width)

        # Margen derecho extra si el pet está visible
        right_margin = 22 + (100 if s.pet_enabled and s.pet_url else 0)
        self._outer.setContentsMargins(22, 16, right_margin, 16)

        # Indicador (SÍ usa el color de acento)
        self.indicator.setStyleSheet(f"color: {s.accent}; font-size: 10px;")

        # Estado (neutro)
        self.status_label.setStyleSheet(
            "color: rgba(255,255,255,100); font-size: 11px; background: transparent;"
        )

        # Fuente japonés (neutro, no el acento)
        jp_f = QFont(s.jp_font, s.jp_size)
        jp_f.setWeight(QFont.Weight.Light)
        self.jp_label.setFont(jp_f)
        self.jp_label.setStyleSheet(
            "color: rgba(255,255,255,140); background: transparent;"
        )

        # Fuente español
        es_f = QFont(s.es_font, s.es_size)
        self.es_label.setFont(es_f)
        self.es_label.setStyleSheet("color: white; background: transparent;")

        # Línea
        self.loading_line.set_accent(a)

        # Pet
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

        # Repintar borde
        self.update()

    # ── Pet GIF ────────────────────────────────

    def _download_pet_gif(self, url: str):
        """Descarga un GIF animado y lo reproduce en el pet_label."""
        self._net = QNetworkAccessManager()
        req = QNetworkRequest(QUrl(url))
        reply = self._net.get(req)
        reply.finished.connect(lambda r=reply: self._on_pet_loaded(r))

    def _on_pet_loaded(self, reply):
        data = reply.readAll()
        if not data or data.isEmpty():
            return
        self._pet_path = f"/tmp/n1_pet_{id(self)}.gif"
        with open(self._pet_path, "wb") as f:
            f.write(bytes(data))
        if self._pet_movie:
            self._pet_movie.stop()
        self._pet_movie = QMovie(self._pet_path)
        self._pet_movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._pet_movie.setScaledSize(self._pet_label.size())
        self._pet_label.setMovie(self._pet_movie)
        self._pet_movie.start()

    # ── Animaciones ───────────────────────────

    def _setup_animations(self):
        self._pulse_anim = QPropertyAnimation(self, b"pulse_val")
        self._pulse_anim.setDuration(1600)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setKeyValueAt(0.0, 0.35)
        self._pulse_anim.setKeyValueAt(0.5, 1.0)
        self._pulse_anim.setKeyValueAt(1.0, 0.35)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.start()

        if _CAN_FADE:
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self._fade_anim.setDuration(180)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        else:
            self._fade_anim = None

    # ── Blur ─────────────────────────────────

    def _setup_blur(self):
        try:
            from PySide6.QtX11Extras import QX11Info
            if QX11Info.isPlatformX11():
                import ctypes, ctypes.util
                so = ctypes.util.find_library("xcb")
                if so:
                    xcb = ctypes.cdll.LoadLibrary(so)
                    conn = xcb.xcb_connect(None, None)
                    if conn:
                        xcb.xcb_intern_atom(conn, 0,
                            len(b"_KDE_NET_WM_BLUR_BEHIND_REGION"),
                            b"_KDE_NET_WM_BLUR_BEHIND_REGION")
                        xcb.xcb_disconnect(conn)
        except Exception:
            pass

    # ── Paint ────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), 14, 14)
        painter.setBrush(QColor(8, 8, 14, 215))
        a = self._acc
        painter.setPen(QPen(QColor(a.red(), a.green(), a.blue(), 35), 1))
        painter.drawPath(path)

    # ── Ajustes desde fuera ──────────────────

    def update_settings(self, s: AppSettings):
        """Aplica una nueva configuración y refresca la UI."""
        self._settings = s
        self._acc = s.accent_qcolor()
        self._apply_settings_to_ui()

        # Re-posicionar por si cambió el ancho
        self.move_to_position()

    # ── Métodos públicos ─────────────────────

    def show_translation(self, jp_text: str, es_text: str):
        self.jp_label.setText(jp_text.strip())
        self.es_label.setText(es_text.strip())
        self.es_label.setStyleSheet("color: white; background: transparent;")
        self.status_label.setText("　Traducción lista")
        self.loading_line.stop_loading()
        self._restart_pulse()
        self._resize_to_content()

    def show_translating(self):
        self.status_label.setText("　Traduciendo…")
        self.loading_line.start_loading()

    def show_error(self, msg: str):
        self.es_label.setText(f"⚠ {msg}")
        self.es_label.setStyleSheet("color: #ef4444; background: transparent;")
        self.status_label.setText("　Error")
        self.status_label.setStyleSheet("color: rgba(239,68,68,150); font-size: 11px; background: transparent;")
        self.loading_line.stop_loading()
        self._restart_pulse()
        self._resize_to_content()

    def show_idle(self):
        self.jp_label.setText("　")
        self.es_label.setText("　")
        self.status_label.setText("　En espera…")
        self.loading_line.stop_loading()
        self._resize_to_content()

    # ── Auto-expand ──────────────────────────

    def _resize_to_content(self):
        self.adjustSize()
        self.move_to_position()

    # ── Posición ──────────────────────────────

    def move_to_position(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 20
        y = geo.bottom() - self.height() - 20
        self.move(x, y)

    # ── Show / Hide ───────────────────────────

    def show_overlay(self):
        self.move_to_position()
        if self._fade_anim:
            self._fade_anim.stop()
            self._fade_anim.setDirection(QPropertyAnimation.Direction.Forward)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        else:
            self.setWindowOpacity(1.0)
        if not self.isVisible():
            self.show()
            self.raise_()

    def hide_overlay(self):
        if self._fade_anim:
            self._fade_anim.stop()
            self._fade_anim.finished.connect(
                self._on_hide_done, Qt.ConnectionType.UniqueConnection
            )
            self._fade_anim.setDirection(QPropertyAnimation.Direction.Backward)
            self._fade_anim.setStartValue(1.0)
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.start()
        else:
            self.hide()

    def _on_hide_done(self):
        self.hide()
        if self._fade_anim:
            self._fade_anim.setDirection(QPropertyAnimation.Direction.Forward)

    def mousePressEvent(self, event):
        # Click en la barra superior (puntito + estado) → menú
        if event.position().y() < 28:
            self._show_quick_menu(event)
            return

        # Click en el contenido → copiar traducción
        es = self.es_label.text()
        if es and "⚠" not in es and es.strip() and es != "　":
            cb = QApplication.clipboard()
            cb.setText(es)

    def _show_quick_menu(self, event):
        """Menú flotante que aparece al tocar la barra superior del overlay."""
        menu = QMenu(self)

        act_settings = menu.addAction("⚙ Ajustes")
        act_settings.triggered.connect(self.settings_requested.emit)

        act_test = menu.addAction("🧪 Test: 勉強しています")
        act_test.triggered.connect(self.test_requested.emit)

        menu.addSeparator()

        act_toggle = menu.addAction("🔛 Pausar / Activar")
        act_toggle.triggered.connect(self.toggle_requested.emit)

        menu.addSeparator()

        act_quit = menu.addAction("✕ Salir")
        act_quit.triggered.connect(self.quit_requested.emit)

        menu.exec(event.globalPosition().toPoint())

    # ── Property pulso ───────────────────────

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
