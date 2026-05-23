import sys
import re
import signal
import logging

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QTimer, QProcess

from takoyomi.overlay import TranslatorPopup
from takoyomi.settings import AppSettings, SettingsDialog
from takoyomi.i18n import get as _

logging.basicConfig(
    level=logging.INFO,
    format="[Takoyomi] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("takoyomi")

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
        self._app.setApplicationName("Takoyomi")
        self._app.setOrganizationName("takoyomi-tools")
        self._app.setApplicationDisplayName("Takoyomi")
        self._app.setDesktopFileName("takoyomi")
        self._app.setQuitOnLastWindowClosed(False)

        self._settings = AppSettings()
        self._init_translators()

        self._overlay = TranslatorPopup()
        self._overlay.update_settings(self._settings)
        self._overlay.settings_requested.connect(self._open_settings)
        self._overlay.test_requested.connect(self._test)
        self._overlay.toggle_requested.connect(self._toggle_service_from_menu)
        self._overlay.quit_requested.connect(self._quit)

        self._cache: dict[str, str] = {}
        self._enabled = True
        self._last_text = ""

        self._setup_tray()

        self._overlay.show_idle()
        self._overlay.show_overlay()

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self._polling = False
        self._klipper = None
        self._wl_poll()

    def _init_translators(self):
        tgt = self._settings.target_language
        if _HAS_TRANSLATOR:
            self._ja_to_tgt = GoogleTranslator(source="ja", target=tgt)
            self._tgt_to_ja = GoogleTranslator(source=tgt, target="ja")
        else:
            self._ja_to_tgt = None
            self._tgt_to_ja = None

    def _wl_poll(self):
        if self._polling or not self._enabled:
            QTimer.singleShot(300, self._wl_poll)
            return
        self._polling = True
        text = self._klipper_text()
        if not text:
            text = self._read_wl_paste()
        log.debug(f"clip: {text[:40]!r} (last={self._last_text[:40]!r})")
        if text and text != self._last_text:
            self._process_text(text)
        self._polling = False
        QTimer.singleShot(300, self._wl_poll)

    def _klipper_text(self) -> str:
        if self._klipper is None:
            try:
                import dbus
                bus = dbus.SessionBus()
                self._klipper = bus.get_object('org.kde.klipper', '/klipper')
            except Exception:
                self._klipper = False
        if not self._klipper:
            return ""
        try:
            text = self._klipper.getClipboardContents(
                dbus_interface='org.kde.klipper.klipper'
            )
            return str(text) if text else ""
        except Exception:
            return ""

    def _read_wl_paste(self) -> str:
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

    def _setup_tray(self):
        icon = self._make_icon()
        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip(_("tray_idle", self._settings.ui_language))
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._overlay.isVisible():
                self._overlay.hide_overlay()
            else:
                self._overlay.show_overlay()

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
        self._settings.load()
        self._overlay.update_settings(self._settings)
        self._init_translators()
        ui = self._settings.ui_language
        st = _("tray_paused", ui) if not self._enabled else _("tray_idle", ui)
        self._tray.setToolTip(st)
        log.info(_("settings_applied", ui))

    def _test(self):
        ui = self._settings.ui_language
        if not _HAS_TRANSLATOR:
            self._overlay.show_error(_("not_installed", ui))
            return
        self._test_toggle = not getattr(self, "_test_toggle", False)
        try:
            if self._test_toggle:
                src = _("test_ja_src", ui)
                res = self._ja_to_tgt.translate(src)
                self._overlay.show_translation(src, res)
            else:
                src = _("test_es_src", ui)
                res = self._tgt_to_ja.translate(src)
                self._overlay.show_translation(res, src)
            log.info(f"{_('test_ok', ui)}")
        except Exception as e:
            log.error(f"Test: {e}")
            self._overlay.show_error(str(e))

    def _process_text(self, text: str):
        if len(text) < 2:
            return
        has_jp = bool(RE_JAPANESE.search(text))
        if has_jp:
            translator = self._ja_to_tgt
        else:
            translator = self._tgt_to_ja
        if not translator:
            self._overlay.show_error(_("not_installed", self._settings.ui_language))
            return
        log.info(f"{'JP→TGT' if has_jp else 'TGT→JP'}: {text[:60]}")
        self._last_text = text
        self._overlay.show_translating()
        if text in self._cache:
            result = self._cache[text]
            log.info(f"→ (cache) {result[:80]}")
            if has_jp:
                self._overlay.show_translation(text, result)
            else:
                self._overlay.show_translation(result, text)
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
            else:
                self._overlay.show_error(_("no_result", self._settings.ui_language))
        except Exception as exc:
            log.error(f"Error: {exc}")
            self._overlay.show_error(str(exc))
            self._last_text = ""

    def _toggle_service_from_menu(self):
        self._enabled = not self._enabled
        st = _("tray_paused", self._settings.ui_language) if not self._enabled else _("tray_idle", self._settings.ui_language)
        self._tray.setToolTip(st)

    def _quit(self):
        self._tray.hide()
        self._app.quit()

    @staticmethod
    def _make_icon() -> QIcon:
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(168, 85, 247))
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
