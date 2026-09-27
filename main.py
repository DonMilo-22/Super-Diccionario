import sys

from pynput import keyboard
from PyQt6.QtCore import QPoint, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCursor, QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QGraphicsOpacityEffect,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from capture import CaptureOverlay
from dialogs import HistoryDialog, SettingsDialog
from dictionary import auto_suggestions, english, ends_with, generate_suggestions, spanish
from ocr import OCRUnavailableError, correction_candidates
from platform_utils import get_foreground_target, set_autostart, target_name, type_text
from settings import apply_profile, load_settings, save_settings
from stats import load_stats, record_word, start_session, toggle_favorite
from used_words import add_used, clear_used


class WordFinder(QWidget):
    capture_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.last_target = None
        self.capture_overlay = None
        self.result_words = []
        self.session_app_name = ""

        self.setWindowTitle("Word Helper")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(390, 460)

        self.apply_theme()
        self.build_ui()
        self.connect_events()
        self.setup_numeric_shortcuts()
        self.capture_requested.connect(self.start_capture)
        self.refresh_stats()

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget { background:#17171A; color:#F4F4F6; font-family:Arial,sans-serif; font-size:13px; }
            QLineEdit, QComboBox { background:#242428; border:1px solid #393940; border-radius:10px; padding:8px; }
            QPushButton { background:#2D2D33; border:1px solid #3A3A42; border-radius:10px; padding:8px; font-weight:600; }
            QPushButton:hover { background:#3A3A42; }
            QListWidget { background:#202024; border:1px solid #34343A; border-radius:12px; padding:5px; outline:none; }
            QListWidget::item { padding:10px; margin:2px; border-radius:8px; }
            QListWidget::item:hover { background:#303038; }
            QListWidget::item:selected { background:#5753D7; }
            QLabel#muted { color:#9A9AA6; font-size:11px; }
        """)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Roblox", "English", "Español", "Ambos"])
        self.profile_combo.setCurrentText(self.settings.get("profile", "Roblox"))

        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedWidth(42)
        self.history_button = QPushButton("Historial")
        top.addWidget(self.profile_combo, 1)
        top.addWidget(self.history_button)
        top.addWidget(self.settings_button)
        layout.addLayout(top)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Alt + Espacio para capturar, o escribe aquí…")
        layout.addWidget(self.input_box)

        controls = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["auto", "start", "end"])
        self.mode_combo.setCurrentText(self.settings.get("search_mode", "auto"))

        self.language_combo = QComboBox()
        self.language_combo.addItems(["english", "spanish", "both"])
        self.language_combo.setCurrentText(self.settings.get("language", "both"))

        self.new_session_button = QPushButton("Nueva partida")
        controls.addWidget(self.mode_combo)
        controls.addWidget(self.language_combo)
        controls.addWidget(self.new_session_button)
        layout.addLayout(controls)

        self.results = QListWidget()
        self.results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.results, 1)

        self.status_label = QLabel("Alt + Espacio · 1–9 para elegir · clic derecho para favorito")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("muted")
        layout.addWidget(self.stats_label)

    def connect_events(self):
        self.input_box.returnPressed.connect(self.search)
        self.results.itemClicked.connect(self.choose_item)
        self.results.customContextMenuRequested.connect(self.open_result_menu)
        self.settings_button.clicked.connect(self.open_settings)
        self.history_button.clicked.connect(self.open_history)
        self.new_session_button.clicked.connect(lambda: self.new_session(True))
        self.profile_combo.currentTextChanged.connect(self.profile_changed)
        self.mode_combo.currentTextChanged.connect(self.quick_setting_changed)
        self.language_combo.currentTextChanged.connect(self.quick_setting_changed)

    def setup_numeric_shortcuts(self):
        self.number_shortcuts = []
        for number in range(1, 10):
            shortcut = QShortcut(QKeySequence(str(number)), self)
            shortcut.activated.connect(lambda n=number: self.choose_number(n))
            self.number_shortcuts.append(shortcut)

    def profile_changed(self, profile):
        self.settings = apply_profile(self.settings, profile)
        self.mode_combo.setCurrentText(self.settings["search_mode"])
        self.language_combo.setCurrentText(self.settings["language"])
        save_settings(self.settings)

    def quick_setting_changed(self):
        self.settings["search_mode"] = self.mode_combo.currentText()
        self.settings["language"] = self.language_combo.currentText()
        save_settings(self.settings)

    def start_capture(self, target=None):
        if target:
            self.last_target = target
            self.handle_session_target(target)

        self.hide()
        QTimer.singleShot(100, self.open_capture_overlay)

    def handle_session_target(self, target):
        name = target_name(target)
        if not name:
            return

        is_roblox = "roblox" in name.lower()
        previous_was_roblox = "roblox" in self.session_app_name.lower()

        if is_roblox and not previous_was_roblox and self.settings.get("reset_on_new_session", True):
            self.new_session(True, show_message=False)

        self.session_app_name = name

    def open_capture_overlay(self):
        self.capture_overlay = CaptureOverlay()
        self.capture_overlay.captured.connect(self.process_capture)
        self.capture_overlay.cancelled.connect(self.capture_cancelled)
        self.capture_overlay.show_capture()

    def capture_cancelled(self):
        self.capture_overlay = None
        self.show_normal()
        self.status_label.setText("Captura cancelada.")

    def process_capture(self, capture_file):
        self.capture_overlay = None
        try:
            from ocr import read_text
            raw_text = read_text(capture_file)
        except OCRUnavailableError as exc:
            self.show_normal()
            QMessageBox.warning(self, "OCR no disponible", str(exc))
            return
        except Exception as exc:
            self.show_normal()
            QMessageBox.warning(self, "Error de OCR", str(exc))
            return

        candidates = correction_candidates(raw_text)
        fragment, confidence = self.pick_best_ocr_candidate(candidates)

        if not fragment:
            self.show_normal()
            self.results.clear()
            self.status_label.setText("No se detectó texto útil.")
            return

        self.input_box.setText(fragment)
        self.search(show_after=True)
        confidence_text = {"high": "alta", "medium": "media", "low": "baja"}.get(confidence, confidence)
        self.status_label.setText(
            f'OCR: "{fragment}" · confianza {confidence_text} · {len(self.result_words)} opciones'
        )

    def pick_best_ocr_candidate(self, candidates):
        best = ""
        best_count = -1
        for candidate in candidates:
            count = len(self.find_words(candidate, limit=20))
            if count > best_count:
                best = candidate
                best_count = count

        if best_count >= 6:
            confidence = "high"
        elif best_count >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        return best, confidence

    def search_options(self):
        return {
            "min_length": int(self.settings.get("min_length", 1)),
            "max_length": int(self.settings.get("max_length", 32)),
            "exclude_proper": bool(self.settings.get("exclude_proper_names", False)),
            "common_first": bool(self.settings.get("common_words_first", True)),
            "smart_antirepeat": bool(self.settings.get("smart_antirepeat", True)),
        }

    def selected_dictionaries(self):
        language = self.language_combo.currentText()
        if language == "english":
            return [("🇺🇸", english)]
        if language == "spanish":
            return [("🇪🇸", spanish)]
        return [("🇺🇸", english), ("🇪🇸", spanish)]

    def find_words(self, fragment, limit=9):
        mode = self.mode_combo.currentText()
        options = self.search_options()
        combined = []
        seen = set()

        for flag, words in self.selected_dictionaries():
            if mode == "start":
                matches = generate_suggestions(fragment, words, limit=limit, **options)
            elif mode == "end":
                matches = ends_with(fragment, words, limit=limit, **options)
            else:
                matches = auto_suggestions(fragment, words, limit=limit, **options)

            for word in matches:
                key = word.lower()
                if key not in seen:
                    combined.append((word, flag))
                    seen.add(key)

        return combined[:limit]

    def search(self, show_after=False):
        fragment = self.input_box.text().strip()
        if not fragment:
            return

        matches = self.find_words(fragment, limit=9)
        self.result_words = [word for word, _flag in matches]
        self.results.clear()

        stats = load_stats()
        favorites = set(stats.get("favorites", []))

        for index, (word, flag) in enumerate(matches, start=1):
            star = "★ " if word.lower() in favorites else ""
            item = QListWidgetItem(f"{index}   {star}{word}  {flag}")
            item.setData(Qt.ItemDataRole.UserRole, word)
            item.setToolTip("Clic para escribir · clic derecho para favorito")
            self.results.addItem(item)

        if len(matches) == 1 and self.settings.get("auto_select_single", False):
            QTimer.singleShot(100, lambda: self.choose_word(matches[0][0]))
            return

        if show_after:
            if self.settings.get("compact_overlay", True):
                self.show_compact()
            else:
                self.show_normal()

        self.status_label.setText(f"{len(matches)} sugerencias · 1–9 para elegir")

    def show_compact(self):
        self.resize(350, min(430, 170 + self.results.count() * 46))
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()

        x = min(cursor.x() + 18, area.right() - self.width())
        y = min(cursor.y() + 18, area.bottom() - self.height())
        self.move(QPoint(max(area.left(), x), max(area.top(), y)))
        self.fade_in()
        self.raise_()
        self.activateWindow()

    def fade_in(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(120)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.finished.connect(lambda: self.setGraphicsEffect(None))
        self._fade_animation = animation
        self.show()
        animation.start()

    def show_normal(self):
        self.resize(390, 460)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 14, screen.bottom() - self.height() - 14)
        self.show()
        self.raise_()
        self.activateWindow()

    def choose_number(self, number):
        if 1 <= number <= len(self.result_words):
            self.choose_word(self.result_words[number - 1])

    def choose_item(self, item):
        word = item.data(Qt.ItemDataRole.UserRole)
        if word:
            self.choose_word(word)

    def choose_word(self, word):
        add_used(word)
        record_word(word)
        self.refresh_stats()

        target = self.last_target
        self.hide()

        if self.settings.get("sound_feedback", True):
            QApplication.beep()

        QTimer.singleShot(
            90,
            lambda: self.type_selected_word(word, target),
        )

    def type_selected_word(self, word, target):
        try:
            type_text(
                word,
                target,
                press_enter=bool(self.settings.get("auto_enter", False)),
            )
        except Exception as exc:
            QGuiApplication.clipboard().setText(word)
            self.show_normal()
            QMessageBox.warning(
                self,
                "No se pudo escribir automáticamente",
                f'"{word}" se copió al portapapeles.\n\n{exc}',
            )

    def open_result_menu(self, position):
        item = self.results.itemAt(position)
        if not item:
            return
        word = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        favorite_action = menu.addAction("★ Agregar/quitar favorito")
        selected = menu.exec(self.results.mapToGlobal(position))
        if selected == favorite_action:
            toggle_favorite(word)
            self.search()

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            old_hotkey = self.settings.get("hotkey")
            old_autostart = self.settings.get("start_with_system", False)
            self.settings = dialog.values()
            save_settings(self.settings)

            self.profile_combo.setCurrentText(self.settings["profile"])
            self.mode_combo.setCurrentText(self.settings["search_mode"])
            self.language_combo.setCurrentText(self.settings["language"])

            if old_autostart != self.settings.get("start_with_system", False):
                try:
                    set_autostart(self.settings["start_with_system"])
                except Exception as exc:
                    QMessageBox.warning(self, "Inicio automático", str(exc))

            if old_hotkey != self.settings.get("hotkey"):
                restart_global_hotkey(self.settings["hotkey"])

    def open_history(self):
        dialog = HistoryDialog(self)
        dialog.exec()
        if self.input_box.text().strip():
            self.search()

    def new_session(self, clear_words=True, show_message=True):
        if clear_words:
            clear_used()
        start_session()
        self.results.clear()
        self.result_words = []
        self.refresh_stats()
        if show_message:
            self.status_label.setText("Nueva partida iniciada. Palabras usadas reiniciadas.")

    def refresh_stats(self):
        stats = load_stats()
        self.stats_label.setText(
            f'Sesión: {stats.get("session_words", 0)} palabras · '
            f'Total: {stats.get("total_words", 0)} · '
            f'Sesiones: {stats.get("sessions", 0)}'
        )

    def closeEvent(self, event):
        event.ignore()
        self.hide()


window = None
listener = None


def on_activate():
    if window:
        target = get_foreground_target()
        window.capture_requested.emit(target)


def restart_global_hotkey(hotkey_text=None):
    global listener
    if listener:
        listener.stop()
        listener = None

    hotkey_text = hotkey_text or load_settings().get("hotkey", "<alt>+<space>")
    hotkey = keyboard.HotKey(keyboard.HotKey.parse(hotkey_text), on_activate)

    def canonical(function):
        return lambda key: function(listener.canonical(key))

    listener = keyboard.Listener(
        on_press=canonical(hotkey.press),
        on_release=canonical(hotkey.release),
    )
    listener.start()


def create_tray(app):
    tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
    tray.setToolTip("Word Helper")

    menu = QMenu()
    show_action = QAction("Abrir Word Helper", menu)
    capture_action = QAction("Capturar ahora", menu)
    session_action = QAction("Nueva partida", menu)
    quit_action = QAction("Salir", menu)

    show_action.triggered.connect(window.show_normal)
    capture_action.triggered.connect(lambda: window.start_capture(get_foreground_target()))
    session_action.triggered.connect(lambda: window.new_session(True))
    quit_action.triggered.connect(app.quit)

    menu.addAction(show_action)
    menu.addAction(capture_action)
    menu.addAction(session_action)
    menu.addSeparator()
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.show_normal()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()
    return tray


def main():
    global window

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WordFinder()
    window.hide()
    start_session()

    restart_global_hotkey(window.settings.get("hotkey"))
    tray = create_tray(app)
    app._wordhelper_tray = tray

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
