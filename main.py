#!/usr/bin/env python3
"""
N1 Translator — Overlay transparente SIEMPRE visible.
Traduce japonés → español desde el portapapeles en vivo.
"""

import sys
import re
import signal
import logging

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QTimer, QProcess

from popup import TranslatorPopup
from settings import AppSettings, SettingsDialog

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


class TranslatorApp:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("N1 Translator")
        self._app.setOrganizationName("n1-tools")
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

        # Traductor
        self._translator = (
            GoogleTranslator(source="ja", target="es")
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

        # Portapapeles
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._wl_poll)
        self._poll_timer.start(200)

        # Arranque
        self._overlay.show_idle()
        self._overlay.show_overlay()

        signal.signal(signal.SIGINT, signal.SIG_DFL)

    # ── wl-paste ──────────────────────────────

    def _wl_poll(self):
        if not self._enabled:
            return
        try:
            proc = QProcess()
            proc.start("wl-paste", ["--type", "text/plain"])
            if proc.waitForFinished(50):
                raw = proc.readAllStandardOutput()
                text = bytes(raw).decode("utf-8", errors="replace").strip()
                if text and text != self._last_text:
                    self._process_text(text)
        except Exception as exc:
            log.debug(f"wl-paste: {exc}")

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
        dialog = SettingsDialog(self._settings, self._overlay)
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.applied.connect(self._on_settings_applied)

        # Centrar en la pantalla
        screen = self._app.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            dialog.move(
                sg.center().x() - dialog.width() // 2,
                sg.center().y() - dialog.height() // 2,
            )
        dialog.open()  # open() en vez de exec() — más confiable en Wayland

    def _on_settings_applied(self):
        self._settings.load()  # recarga desde QSettings
        self._overlay.update_settings(self._settings)
        log.info("⚙ Ajustes aplicados")

    # ── Test ──────────────────────────────────

    def _test(self):
        log.info("🧪 Test manual")
        if self._translator:
            try:
                result = self._translator.translate("勉強しています")
                log.info(f"→ {result}")
                self._cache["勉強しています"] = result
                self._last_jp = "勉強しています"
                self._last_es = result
                self._overlay.show_translation("勉強しています", result)
                self._tray.showMessage(
                    "N1 Translator", f"→ {result}",
                    QSystemTrayIcon.MessageIcon.Information, 5000,
                )
            except Exception as e:
                log.error(f"Test: {e}")
                self._overlay.show_error(str(e))
        else:
            self._overlay.show_error("deep-translator no instalado")

    # ── Traducción ────────────────────────────

    def _process_text(self, text: str):
        if len(text) < 2:
            return
        if not RE_JAPANESE.search(text):
            return

        log.info(f"✅ Japonés: {text[:60]}")
        self._last_text = text
        self._overlay.show_translating()

        # Cache hit
        if text in self._cache:
            result = self._cache[text]
            log.info(f"→ (cache) {result[:80]}")
            self._last_jp = text
            self._last_es = result
            self._overlay.show_translation(text, result)
            self._tray.setToolTip(
                f"N1 ● {text[:15]}… → {result[:15]}…"
            )
            return

        if not self._translator:
            self._overlay.show_error("deep-translator no instalado")
            return

        try:
            result = self._translator.translate(text)
            log.info(f"→ {result[:80]}")
            if result and result.strip():
                self._cache[text] = result
                self._last_jp = text
                self._last_es = result
                self._overlay.show_translation(text, result)
                self._tray.setToolTip(
                    f"N1 ● {text[:15]}… → {result[:15]}…"
                )
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


if __name__ == "__main__":
    TranslatorApp().run()
