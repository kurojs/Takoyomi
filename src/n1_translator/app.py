"""
app.py — Application entry point, system tray, clipboard polling, translation pipeline.
"""

import sys
import re
import signal
import logging

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QTimer, QProcess

from n1_translator.overlay import TranslatorPopup
from n1_translator.settings import AppSettings, SettingsDialog

logging.basicConfig(
    level=logging.DEBUG,
    format="[N1] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("n1")

try:
    from deep_translator import GoogleTranslator
    _HAS_TRANSLATOR = True
except ImportError:
    _HAS_TRANSLATOR = False


RE_JAPANESE = re.compile(
    r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff'
    r'\uff00-\uffef\u4e00-\u9fff\u3400-\u4dbf]'
)
RE_SPANISH = re.compile(
    r'[áéíóúüñÁÉÍÓÚÜÑ¿¡]'
)


class TranslatorApp:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("N1 Translator")
        self._app.setOrganizationName("n1-tools")
        self._app.setApplicationDisplayName("N1 Translator")
        self._app.setDesktopFileName("n1-translator")
        self._app.setQuitOnLastWindowClosed(False)

        # Settings persistentes
        self._settings = AppSettings()

        # Overlay
        self._overlay = TranslatorPopup()
        self._overlay.update_settings(self._settings)
        self._overlay.settings_requested.connect(self._open_settings)
        self._overlay.test_requested.connect(self._test)
        self._overlay.toggle_requested.connect(self._toggle_service_from_menu)
        self._overlay.quit_requested.connect(self._quit)

        # Traductores (bidireccional)
        self._ja_to_es = (
            GoogleTranslator(source="ja", target="es")
            if _HAS_TRANSLATOR else None
        )
        self._es_to_ja = (
            GoogleTranslator(source="es", target="ja")
            if _HAS_TRANSLATOR else None
        )
        self._cache: dict[str, str] = {}

        # Estado
        self._enabled = True
        self._last_text = ""
        self._last_jp = ""
        self._last_es = ""

        # Bandeja
        self._setup_tray()

        # Arranque
        self._overlay.show_idle()
        self._overlay.show_overlay()

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Portapapeles (Klipper DBus + wl-paste fallback)
        self._polling = False
        self._klipper = None  # lazy: se conecta al primer poll
        self._wl_poll()

    # ── Clipboard (Klipper + wl-paste) ────────

    def _wl_poll(self):
        """Lee PRIMARY vía Klipper (~0ms). wl-paste como fallback si Klipper vacío."""
        if self._polling or not self._enabled:
            QTimer.singleShot(300, self._wl_poll)
            return

        self._polling = True

        # Klipper DBus (instantáneo) + wl-paste fallback (PRIMARY + CLIPBOARD)
        text = self._klipper_text()
        if not text:
            text = self._read_wl_paste()

        log.debug(f"clip: {text[:40]!r} (last={self._last_text[:40]!r})")

        if text and text != self._last_text:
            self._process_text(text)

        self._polling = False
        QTimer.singleShot(300, self._wl_poll)

    # ── Klipper DBus (KDE nativo, instantáneo) ─

    def _klipper_text(self) -> str:
        """Lee clipboard desde Klipper vía DBus directo (sin subprocess)."""
        if self._klipper is None:
            try:
                import dbus
                bus = dbus.SessionBus()
                self._klipper = bus.get_object(
                    'org.kde.klipper', '/klipper'
                )
            except Exception:
                self._klipper = False  # marca para no reintentar
        if not self._klipper:
            return ""
        try:
            text = self._klipper.getClipboardContents(
                dbus_interface='org.kde.klipper.klipper'
            )
            return str(text) if text else ""
        except Exception:
            return ""

    # ── wl-paste (fallback) ──────────────────

    def _read_wl_paste(self) -> str:
        """Lee CLIPBOARD + PRIMARY con wl-paste. Fallback si Klipper vacío."""
        for _, args in (
            ("clip",   ["--type", "text/plain"]),
            ("auto",   []),
            ("select", ["--primary"]),
        ):
            try:
                proc = QProcess()
                proc.start("wl-paste", args)
                if proc.waitForFinished(300):
                    raw = proc.readAllStandardOutput()
                    t = bytes(raw).decode("utf-8", errors="replace").strip()
                    if t:
                        return t
            except Exception:
                pass
        return ""

    # ── Bandeja ───────────────────────────────

    def _setup_tray(self):
        icon = self._make_icon()
        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip("N1 Translator ● En espera")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ── Click en bandeja ─────────────────────

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Click izquierdo → toggle overlay
            if self._overlay.isVisible():
                self._overlay.hide_overlay()
            else:
                self._overlay.show_overlay()

    # ── Settings ──────────────────────────────

    def _open_settings(self):
        dialog = SettingsDialog(self._settings)
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.applied.connect(self._on_settings_applied)
        dialog.exec()

    def _on_settings_applied(self):
        self._settings.load()  # recarga desde QSettings
        self._overlay.update_settings(self._settings)
        log.info("⚙ Ajustes aplicados")

    # ── Test ──────────────────────────────────

    def _test(self):
        log.info("🧪 Test manual")

        if not self._ja_to_es or not self._es_to_ja:
            self._overlay.show_error("deep-translator no instalado")
            return

        # Alterna JP→ES / ES→JP en cada click
        self._test_toggle = not getattr(self, "_test_toggle", False)

        try:
            if self._test_toggle:
                src, pair = "勉強しています", "JP→ES"
                res = self._ja_to_es.translate(src)
                self._cache[src] = res
                self._overlay.show_translation(src, res)
            else:
                src, pair = "Estoy aprendiendo japonés", "ES→JP"
                res = self._es_to_ja.translate(src)
                self._cache[src] = res
                self._overlay.show_translation(res, src)

            log.info(f"🧪 {pair}: {src[:30]} → {res[:30]}")
            self._tray.showMessage(
                "N1 Translator", f"{pair} → {res[:30]}",
                QSystemTrayIcon.MessageIcon.Information, 5000,
            )
        except Exception as e:
            log.error(f"Test: {e}")
            self._overlay.show_error(str(e))

    # ── Traducción ────────────────────────────

    def _process_text(self, text: str):
        if len(text) < 2:
            return

        # Detectar dirección
        has_jp = bool(RE_JAPANESE.search(text))
        has_es = bool(RE_SPANISH.search(text))

        if has_jp:
            translator = self._ja_to_es
            direction = "JP→ES"
        elif has_es:
            translator = self._es_to_ja
            direction = "ES→JP"
        else:
            return

        log.info(f"✅ {direction}: {text[:60]}")
        self._last_text = text
        self._overlay.show_translating()

        # Cache hit
        if text in self._cache:
            result = self._cache[text]
            log.info(f"→ (cache) {result[:80]}")
            if has_jp:
                self._overlay.show_translation(text, result)
            else:
                self._overlay.show_translation(result, text)
            self._tray.setToolTip(f"N1 ● {text[:15]}… → {result[:15]}…")
            return

        if not translator:
            self._overlay.show_error("deep-translator no instalado")
            return

        try:
            result = translator.translate(text)
            log.info(f"→ {result[:80]}")
            if result and result.strip():
                self._cache[text] = result
                if has_jp:
                    self._overlay.show_translation(text, result)
                else:
                    self._overlay.show_translation(result, text)
                self._tray.setToolTip(f"N1 ● {text[:15]}… → {result[:15]}…")
            else:
                self._overlay.show_error("Sin resultado")
        except Exception as exc:
            log.error(f"Error: {exc}")
            self._overlay.show_error(str(exc))
            self._last_text = ""

    # ── Servicio ──────────────────────────────

    def _toggle_service_from_menu(self):
        """Toggle sin checkbox (desde el menú del overlay)."""
        self._enabled = not self._enabled
        st = "En espera" if self._enabled else "Pausado"
        self._tray.setToolTip(f"N1 Translator ● {st}")

    def _quit(self):
        self._tray.hide()
        self._app.quit()

    # ── Icono ────────────────────────────────

    @staticmethod
    def _make_icon() -> QIcon:
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(168, 85, 247))  # 🟣 púrpura
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 12, 12)
        p.end()
        return QIcon(pm)

    def run(self):
        sys.exit(self._app.exec())


def run_app():
    app = TranslatorApp()
    app.run()


if __name__ == "__main__":
    run_app()
