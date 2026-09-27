import re
import sys

from pynput import keyboard
from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from capture import CaptureOverlay
from dictionary import english, ends_with, generate_suggestions, spanish
from ocr import OCRUnavailableError, read_text
from platform_utils import get_foreground_target, type_text
from used_words import add_used, clear_used


def normalize_ocr_text(text):
    text = re.sub(r"\s+", "", text or "")
    text = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", text)
    return text.upper()


class WordFinder(QWidget):
    capture_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.last_target = None
        self.capture_overlay = None
        self.current_mode = "start"

        self.setWindowTitle("Word Helper")
        self.resize(460, 520)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.apply_theme()
        self.build_ui()
        self.connect_events()
        self.capture_requested.connect(self.start_capture)
        self.move_to_bottom_right()

    def apply_theme(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1A1A1D;
                color: #F5F5F7;
                font-family: Helvetica, Arial, sans-serif;
                font-size: 13px;
            }

            QLabel {
                color: #F5F5F7;
                font-size: 14px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #25252B;
                border: 2px solid #6C63FF;
                border-radius: 14px;
                padding: 10px;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #6C63FF;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #7A72FF;
            }

            QPushButton:pressed {
                background-color: #5A50E5;
            }

            QListWidget {
                background-color: #25252B;
                border: 1px solid #333340;
                border-radius: 16px;
                padding: 6px;
                outline: none;
            }

            QListWidget::item {
                background-color: #2D2D35;
                padding: 12px;
                margin: 4px;
                border-radius: 8px;
                border-left: 4px solid #6C63FF;
            }

            QListWidget::item:hover {
                background-color: #393944;
            }

            QListWidget::item:selected {
                background-color: #6C63FF;
                color: white;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #6C63FF;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("✨ OCR"))

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Escribe letras o usa Alt + Espacio...")
        layout.addWidget(self.input_box)

        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Inicio")
        self.end_button = QPushButton("Final")
        self.reset_button = QPushButton("Reiniciar")
        self.capture_button = QPushButton("Capturar")

        self.capture_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FF5CA8;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF71B5;
            }
            """
        )

        for button in (
            self.start_button,
            self.end_button,
            self.reset_button,
            self.capture_button,
        ):
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        self.help_label = QLabel(
            "Haz clic en una palabra para escribirla en la ventana anterior y marcarla como usada."
        )
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet(
            "color: #B9B9C4; font-size: 12px; font-weight: normal; padding: 4px;"
        )
        layout.addWidget(self.help_label)

        titles_layout = QHBoxLayout()
        titles_layout.addWidget(QLabel("🇺🇸 English"))
        titles_layout.addWidget(QLabel("🇪🇸 Español"))
        layout.addLayout(titles_layout)

        results_layout = QHBoxLayout()
        self.english_list = QListWidget()
        self.spanish_list = QListWidget()

        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.english_list.setFont(font)
        self.spanish_list.setFont(font)

        results_layout.addWidget(self.english_list)
        results_layout.addWidget(self.spanish_list)
        layout.addLayout(results_layout)

        self.status_label = QLabel("Alt + Espacio: capturar texto")
        self.status_label.setStyleSheet(
            "color: #8D8D99; font-size: 11px; font-weight: normal;"
        )
        layout.addWidget(self.status_label)

    def connect_events(self):
        self.input_box.returnPressed.connect(self.search_start)
        self.start_button.clicked.connect(self.search_start)
        self.end_button.clicked.connect(self.search_end)
        self.reset_button.clicked.connect(self.reset_used_words)
        self.capture_button.clicked.connect(lambda: self.start_capture(None))

        self.english_list.itemClicked.connect(self.choose_word)
        self.spanish_list.itemClicked.connect(self.choose_word)

    def start_capture(self, target=None):
        if target:
            self.last_target = target

        self.hide()
        QTimer.singleShot(120, self.open_capture_overlay)

    def open_capture_overlay(self):
        self.capture_overlay = CaptureOverlay()
        self.capture_overlay.captured.connect(self.process_capture)
        self.capture_overlay.cancelled.connect(self.capture_cancelled)
        self.capture_overlay.show_capture()

    def capture_cancelled(self):
        self.capture_overlay = None
        self.show_and_focus()
        self.status_label.setText("Captura cancelada.")

    def process_capture(self, capture_file):
        self.capture_overlay = None

        try:
            text = read_text(capture_file)
        except OCRUnavailableError as exc:
            self.show_and_focus()
            QMessageBox.warning(self, "OCR no disponible", str(exc))
            return
        except Exception as exc:
            self.show_and_focus()
            QMessageBox.warning(
                self,
                "Error de OCR",
                f"No se pudo leer la captura.\n\n{exc}",
            )
            return

        text = normalize_ocr_text(text)
        self.input_box.setText(text)

        self.show_and_focus()

        if not text:
            self.english_list.clear()
            self.spanish_list.clear()
            self.status_label.setText("No se detectó texto en la captura.")
            return

        self.search_start()
        self.status_label.setText(f'OCR detectó: "{text}"')

    def show_and_focus(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.resize(460, 520)
        self.move_to_bottom_right()

    def move_to_bottom_right(self):
        screen = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()

        x = geometry.x() + geometry.width() - self.width() - 10
        y = geometry.y() + geometry.height() - self.height() - 10
        self.move(x, y)

    def add_result_item(self, list_widget, word):
        item = QListWidgetItem(word)
        item.setSizeHint(QSize(0, 42))
        list_widget.addItem(item)

    def populate_results(self, english_results, spanish_results):
        self.english_list.clear()
        self.spanish_list.clear()

        for word in english_results:
            self.add_result_item(self.english_list, word)

        for word in spanish_results:
            self.add_result_item(self.spanish_list, word)

        total = len(english_results) + len(spanish_results)
        self.status_label.setText(f"{total} sugerencias encontradas.")

    def search_start(self):
        text = self.input_box.text().strip()
        if not text:
            return

        self.current_mode = "start"
        self.populate_results(
            generate_suggestions(text, english),
            generate_suggestions(text, spanish),
        )

    def search_end(self):
        text = self.input_box.text().strip()
        if not text:
            return

        self.current_mode = "end"
        self.populate_results(
            ends_with(text, english)[:20],
            ends_with(text, spanish)[:20],
        )

    def choose_word(self, item):
        word = item.text().strip()
        if not word:
            return

        add_used(word)

        for list_widget in (self.english_list, self.spanish_list):
            for row in range(list_widget.count() - 1, -1, -1):
                if list_widget.item(row).text().lower() == word.lower():
                    list_widget.takeItem(row)

        target = self.last_target
        self.status_label.setText(f'Escribiendo "{word}"...')
        self.hide()

        QTimer.singleShot(
            120,
            lambda selected=word, destination=target: self.type_selected_word(
                selected,
                destination,
            ),
        )

    def type_selected_word(self, word, target):
        try:
            type_text(word, target)
        except Exception as exc:
            QGuiApplication.clipboard().setText(word)
            self.show_and_focus()
            QMessageBox.warning(
                self,
                "No se pudo escribir automáticamente",
                (
                    f'La palabra "{word}" ya fue marcada como usada y se copió '
                    "al portapapeles.\n\n"
                    "En macOS revisa el permiso de Accesibilidad para Word Helper.\n"
                    f"Detalle: {exc}"
                ),
            )

    def reset_used_words(self):
        clear_used()
        self.english_list.clear()
        self.spanish_list.clear()
        self.status_label.setText("Lista de palabras usadas reiniciada.")

    def closeEvent(self, event):
        if listener:
            listener.stop()
        event.accept()


window = None
listener = None


def on_activate():
    global window

    if window:
        target = get_foreground_target()
        window.capture_requested.emit(target)


def for_canonical(function):
    return lambda key: function(listener.canonical(key))


def main():
    global window, listener

    app = QApplication(sys.argv)

    window = WordFinder()
    window.show()

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse("<alt>+<space>"),
        on_activate,
    )

    listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release),
    )
    listener.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
