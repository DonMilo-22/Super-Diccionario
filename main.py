import sys
import subprocess
import os
from pynput import keyboard
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QSize
import tempfile
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from ocr import read_text

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel
)

from dictionary import (
    generate_suggestions,
    ends_with,
    english,
    spanish
)

from used_words import (
    add_used,
    clear_used
)


class WordFinder(QWidget):
    capture_requested = pyqtSignal()

    def apply_theme(self):

        self.setStyleSheet("""
    QWidget {
        background-color: #1A1A1D;
        color: #F5F5F7;
        font-family: Helvetica;
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

    QListWidget::item:selected {
        background-color: #6C63FF;
        color: white;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background: #6C63FF;
        border-radius: 5px;
        min-height: 20px;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """)

    def process_capture(self, capture_file):

        self.setWindowOpacity(1)
        self.raise_()
        self.activateWindow()

        if not os.path.exists(capture_file):
            return

        text = read_text(capture_file)

        text = (
            text
            .strip() 
            .replace("\n", "")
            .replace(" ", "")
            .upper()
        )

        self.input_box.setText(text)

        self.search_start()

        self.resize(450, 500)

        self.move_to_bottom_right()
    
    def start_capture(self):

        self.setWindowOpacity(0)

        capture_file = os.path.join(
            tempfile.gettempdir(),
            "wordhelper_capture.png"
        )

        if os.path.exists(capture_file):
            os.remove(capture_file)

        subprocess.run(
            [
                "screencapture",
                "-i",
                capture_file
            ]
        )

        self.process_capture(capture_file)

    def __init__(self):
        super().__init__()
        self.apply_theme()

        self.capture_requested.connect(self.start_capture)

        self.setWindowTitle("Word Helper")
        self.resize(350, 400)

        
        # Siempre encima
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout()

        # Entrada
        ocr_label = QLabel("✨ OCR")
        layout.addWidget(ocr_label)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Escribe letras o texto OCR..."
        )

        layout.addWidget(self.input_box)

        # ENTER = Buscar Inicio
        self.input_box.returnPressed.connect(
            self.search_start
        )

        # Botones
        button_layout = QHBoxLayout()

        self.start_button = QPushButton(
            "Inicio"
        )

        self.end_button = QPushButton(
            "Final"
        )

        self.reset_button = QPushButton(
            "Reiniciar palabras"
        )

        self.capture_button = QPushButton(
            "Capturar"
        )

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.end_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.capture_button)

        layout.addLayout(button_layout)

        # Títulos
        titles_layout = QHBoxLayout()

        english_title = QLabel("🇺🇸 English")
        spanish_title = QLabel("🇪🇸 Español")

        titles_layout.addWidget(english_title)
        titles_layout.addWidget(spanish_title)

        layout.addLayout(titles_layout)

        # Resultados
        results_layout = QHBoxLayout()

        self.english_list = QListWidget()
        self.spanish_list = QListWidget()
        from PyQt6.QtGui import QFont

        font = QFont()
        font.setPointSize(25)
        font.setBold(True)

        self.english_list.setFont(font)
        self.spanish_list.setFont(font)

        results_layout.addWidget(self.english_list)
        results_layout.addWidget(self.spanish_list)

        layout.addLayout(results_layout)

        self.setLayout(layout)

        # Eventos
        self.start_button.clicked.connect(
            self.search_start
        )

        self.end_button.clicked.connect(
            self.search_end
        )

        self.reset_button.clicked.connect(
            self.reset_used_words
        )

        self.capture_button.clicked.connect(
            self.start_capture
        )
        self.capture_button.setStyleSheet("""
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
""")

        self.english_list.itemChanged.connect(
            self.word_checked
        )

        self.spanish_list.itemChanged.connect(
            self.word_checked
        )

        # Mover a esquina inferior derecha
        self.move_to_bottom_right()

    def move_to_bottom_right(self):

        screen = QGuiApplication.primaryScreen()

        geometry = screen.availableGeometry()

        x = geometry.width() - self.width() - 10
        y = geometry.height() - self.height() - 0

        self.move(x, y)

    def add_checkbox_item(
        self,
        list_widget,
        word
    ):

        item = QListWidgetItem(word)
        item.setSizeHint(QSize(0, 40))

        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
        )

        item.setCheckState(
            Qt.CheckState.Unchecked
        )

        list_widget.addItem(item)

    def search_start(self):

        text = self.input_box.text().strip()

        if not text:
            return

        self.english_list.clear()
        self.spanish_list.clear()

        english_results = generate_suggestions(
            text,
            english
        )

        spanish_results = generate_suggestions(
            text,
            spanish
        )

        for word in english_results:
            self.add_checkbox_item(
                self.english_list,
                word
            )

        for word in spanish_results:
            self.add_checkbox_item(
                self.spanish_list,
                word
            )

    def search_end(self):

        text = self.input_box.text().strip()

        if not text:
            return

        self.english_list.clear()
        self.spanish_list.clear()

        english_results = ends_with(
            text,
            english
        )[:20]

        spanish_results = ends_with(
            text,
            spanish
        )[:20]

        for word in english_results:
            self.add_checkbox_item(
                self.english_list,
                word
            )

        for word in spanish_results:
            self.add_checkbox_item(
                self.spanish_list,
                word
            )

    def word_checked(self, item):

        if item.checkState() == Qt.CheckState.Checked:

            add_used(item.text())

            list_widget = item.listWidget()

            row = list_widget.row(item)

            list_widget.takeItem(row)

    def reset_used_words(self):

        clear_used()

        self.english_list.clear()
        self.spanish_list.clear()

        print("Palabras usadas reiniciadas")


window = None

def on_activate():

    global window

    if window:

        print("Atajo detectado")

        window.capture_requested.emit()


hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<alt>+<space>'),
    on_activate
)

listener = None


def for_canonical(f):

    return lambda k: f(
        listener.canonical(k)
    )


listener = keyboard.Listener(
    on_press=for_canonical(
        hotkey.press
    ),
    on_release=for_canonical(
        hotkey.release
    )
)

app = QApplication(sys.argv)

window = WordFinder()

window.show()

listener.start()

sys.exit(app.exec())