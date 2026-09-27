from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from settings import PROFILE_PRESETS
from used_words import load_used, remove_used


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.setWindowTitle("Ajustes de Word Helper")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.profile = QComboBox()
        self.profile.addItems(PROFILE_PRESETS.keys())
        self.profile.setCurrentText(self.settings.get("profile", "Roblox"))

        self.language = QComboBox()
        self.language.addItems(["english", "spanish", "both"])
        self.language.setCurrentText(self.settings.get("language", "both"))

        self.search_mode = QComboBox()
        self.search_mode.addItems(["auto", "start", "end"])
        self.search_mode.setCurrentText(self.settings.get("search_mode", "auto"))

        self.hotkey = QLineEdit(self.settings.get("hotkey", "<alt>+<space>"))

        self.min_length = QSpinBox()
        self.min_length.setRange(1, 50)
        self.min_length.setValue(int(self.settings.get("min_length", 1)))

        self.max_length = QSpinBox()
        self.max_length.setRange(1, 80)
        self.max_length.setValue(int(self.settings.get("max_length", 32)))

        form.addRow("Perfil", self.profile)
        form.addRow("Idioma", self.language)
        form.addRow("Búsqueda", self.search_mode)
        form.addRow("Atajo", self.hotkey)
        form.addRow("Longitud mínima", self.min_length)
        form.addRow("Longitud máxima", self.max_length)
        layout.addLayout(form)

        self.auto_enter = QCheckBox("Enviar Enter después de escribir")
        self.auto_select = QCheckBox("Elegir automáticamente si solo hay una opción")
        self.common_first = QCheckBox("Priorizar palabras comunes")
        self.exclude_proper = QCheckBox("Excluir posibles nombres propios")
        self.sound = QCheckBox("Feedback sonoro")
        self.autostart = QCheckBox("Iniciar Word Helper con el sistema")
        self.compact = QCheckBox("Usar overlay compacto")
        self.reset_session = QCheckBox("Reiniciar palabras al iniciar nueva sesión de Roblox")
        self.smart_antirepeat = QCheckBox("Bloquear variantes cercanas de palabras ya usadas")

        checks = {
            self.auto_enter: "auto_enter",
            self.auto_select: "auto_select_single",
            self.common_first: "common_words_first",
            self.exclude_proper: "exclude_proper_names",
            self.sound: "sound_feedback",
            self.autostart: "start_with_system",
            self.compact: "compact_overlay",
            self.reset_session: "reset_on_new_session",
            self.smart_antirepeat: "smart_antirepeat",
        }

        for widget, key in checks.items():
            widget.setChecked(bool(self.settings.get(key, False)))
            layout.addWidget(widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return {
            **self.settings,
            "profile": self.profile.currentText(),
            "language": self.language.currentText(),
            "search_mode": self.search_mode.currentText(),
            "hotkey": self.hotkey.text().strip() or "<alt>+<space>",
            "min_length": self.min_length.value(),
            "max_length": max(self.min_length.value(), self.max_length.value()),
            "auto_enter": self.auto_enter.isChecked(),
            "auto_select_single": self.auto_select.isChecked(),
            "common_words_first": self.common_first.isChecked(),
            "exclude_proper_names": self.exclude_proper.isChecked(),
            "sound_feedback": self.sound.isChecked(),
            "start_with_system": self.autostart.isChecked(),
            "compact_overlay": self.compact.isChecked(),
            "reset_on_new_session": self.reset_session.isChecked(),
            "smart_antirepeat": self.smart_antirepeat.isChecked(),
        }


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Palabras usadas")
        self.resize(360, 430)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecciona una palabra para volver a habilitarla."))

        self.list = QListWidget()
        layout.addWidget(self.list)

        actions = QHBoxLayout()
        self.restore_button = QPushButton("Restaurar")
        self.refresh_button = QPushButton("Actualizar")
        actions.addWidget(self.restore_button)
        actions.addWidget(self.refresh_button)
        layout.addLayout(actions)

        self.restore_button.clicked.connect(self.restore_selected)
        self.refresh_button.clicked.connect(self.refresh)
        self.list.itemDoubleClicked.connect(lambda _item: self.restore_selected())
        self.refresh()

    def refresh(self):
        self.list.clear()
        self.list.addItems(sorted(load_used()))

    def restore_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        remove_used(item.text())
        self.refresh()
