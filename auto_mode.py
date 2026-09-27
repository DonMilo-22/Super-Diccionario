import os
import re
import tempfile
import time

from PyQt6.QtCore import QObject, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication

from dictionary import chain_candidates, english, spanish
from ocr import read_text
from platform_utils import type_text
from used_words import add_used


WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def extract_words(text):
    return WORD_RE.findall(text or "")


def extract_full_word(text):
    words = extract_words(text)
    return max(words, key=len).lower() if words else ""


def extract_requirement(text):
    words = extract_words(text)
    if not words:
        return ""

    trailing_letters = []
    for token in reversed(words):
        if len(token) == 1:
            trailing_letters.append(token)
        else:
            break

    if len(trailing_letters) >= 2:
        return "".join(reversed(trailing_letters)).lower()

    return words[-1].lower()


def normalize_region(region):
    if not isinstance(region, dict):
        return None
    keys = ("x", "y", "width", "height")
    if not all(key in region for key in keys):
        return None
    values = {key: int(region[key]) for key in keys}
    if values["width"] < 5 or values["height"] < 5:
        return None
    return values


class AutomaticChainEngine(QObject):
    status_changed = pyqtSignal(str)
    turn_detected = pyqtSignal(str, str)
    reply_sent = pyqtSignal(str)
    exhausted = pyqtSignal(str)

    def __init__(self, settings, target=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.target = target
        self.opponent_region = normalize_region(settings.get("auto_opponent_region"))
        self.requirement_region = normalize_region(settings.get("auto_requirement_region"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.active = False
        self.busy = False

        self.stable_opponent = ""
        self.opponent_stable_count = 0
        self.stable_requirement = ""
        self.requirement_stable_count = 0

        self.current_opponent = ""
        self.current_requirement = ""
        self.queue = []
        self.last_reply = ""
        self.sent_at = 0.0
        self.waiting_for_turn_change = False

    def update_settings(self, settings):
        self.settings = settings
        self.opponent_region = normalize_region(settings.get("auto_opponent_region"))
        self.requirement_region = normalize_region(settings.get("auto_requirement_region"))
        if self.active:
            self.timer.setInterval(max(300, int(settings.get("auto_interval_ms", 700))))

    def set_target(self, target):
        self.target = target

    def start(self):
        if not self.opponent_region:
            raise ValueError("Falta seleccionar la zona de la palabra completa del oponente.")
        if not self.requirement_region:
            raise ValueError("Falta seleccionar la zona del requisito de inicio.")

        self.active = True
        self.timer.start(max(300, int(self.settings.get("auto_interval_ms", 700))))
        self.status_changed.emit("Modo automático activo")

    def stop(self):
        self.active = False
        self.timer.stop()
        self.busy = False
        self.current_opponent = ""
        self.current_requirement = ""
        self.queue = []
        self.waiting_for_turn_change = False
        self.status_changed.emit("Modo automático detenido")

    def capture_region(self, region, filename):
        center = QPoint(
            region["x"] + region["width"] // 2,
            region["y"] + region["height"] // 2,
        )
        screen = QGuiApplication.screenAt(center) or QGuiApplication.primaryScreen()
        geometry = screen.geometry()

        pixmap = screen.grabWindow(
            0,
            region["x"] - geometry.x(),
            region["y"] - geometry.y(),
            region["width"],
            region["height"],
        )

        path = os.path.join(tempfile.gettempdir(), filename)
        return path if pixmap.save(path, "PNG") else None

    def _stable_value(self, value, current_value, count):
        if not value:
            return "", 0
        if value == current_value:
            return current_value, count + 1
        return value, 1

    def tick(self):
        if not self.active or self.busy:
            return

        self.busy = True
        try:
            opponent_path = self.capture_region(
                self.opponent_region,
                "wordhelper_auto_opponent.png",
            )
            requirement_path = self.capture_region(
                self.requirement_region,
                "wordhelper_auto_requirement.png",
            )
            if not opponent_path or not requirement_path:
                return

            opponent = extract_full_word(read_text(opponent_path))
            requirement = extract_requirement(read_text(requirement_path))

            self.stable_opponent, self.opponent_stable_count = self._stable_value(
                opponent,
                self.stable_opponent,
                self.opponent_stable_count,
            )
            self.stable_requirement, self.requirement_stable_count = self._stable_value(
                requirement,
                self.stable_requirement,
                self.requirement_stable_count,
            )

            stable_reads = max(2, int(self.settings.get("auto_stable_reads", 2)))
            if (
                self.opponent_stable_count < stable_reads
                or self.requirement_stable_count < stable_reads
            ):
                return

            self.handle_turn(self.stable_opponent, self.stable_requirement)
        except Exception as exc:
            self.status_changed.emit(f"Auto: {exc}")
        finally:
            self.busy = False

    def handle_turn(self, opponent_word, requirement):
        now = time.monotonic()

        if self.waiting_for_turn_change:
            if opponent_word != self.current_opponent:
                self.waiting_for_turn_change = False
                self.queue = []
                self.last_reply = ""
            elif requirement != self.current_requirement:
                # The game changed the prompt after our answer. Treat that as
                # acceptance and wait for the opponent's next complete word.
                return
            else:
                retry_ms = int(self.settings.get("auto_retry_ms", 1800))
                if (now - self.sent_at) * 1000 >= retry_ms:
                    self.send_next()
                return

        if (
            opponent_word == self.current_opponent
            and requirement == self.current_requirement
        ):
            return

        self.begin_turn(opponent_word, requirement)

    def begin_turn(self, opponent_word, requirement):
        self.current_opponent = opponent_word.lower()
        self.current_requirement = requirement.lower()

        # Store the full opponent word, never only its suffix or prompt.
        add_used(self.current_opponent)

        language = self.settings.get(
            "auto_language",
            self.settings.get("language", "english"),
        )
        dictionaries = []
        if language in ("english", "both"):
            dictionaries.append(english)
        if language in ("spanish", "both"):
            dictionaries.append(spanish)

        candidates = []
        seen = set()
        for words in dictionaries:
            for word in chain_candidates(
                self.current_requirement,
                words,
                difficulty=self.settings.get("difficulty", "normal"),
                limit=100,
                min_length=int(self.settings.get("min_length", 1)),
                max_length=int(self.settings.get("max_length", 32)),
                smart_antirepeat=bool(self.settings.get("smart_antirepeat", True)),
            ):
                key = word.lower()
                if key not in seen and key != self.current_opponent:
                    candidates.append(word)
                    seen.add(key)

        self.queue = candidates
        self.turn_detected.emit(self.current_opponent, self.current_requirement)
        self.status_changed.emit(
            f"{self.current_opponent} · empieza con {self.current_requirement.upper()} · "
            f"{len(self.queue)} respuestas"
        )

        if not self.queue:
            self.exhausted.emit(self.current_requirement)
            return

        self.send_next()

    def send_next(self):
        if not self.queue:
            self.waiting_for_turn_change = False
            self.exhausted.emit(self.current_requirement)
            return

        word = self.queue.pop(0)
        self.last_reply = word
        add_used(word)

        type_text(
            word,
            self.target,
            delay=float(self.settings.get("auto_type_delay", 0.08)),
            press_enter=True,
        )

        self.sent_at = time.monotonic()
        self.waiting_for_turn_change = True
        self.reply_sent.emit(word)
        self.status_changed.emit(
            f'Probando "{word}" · {len(self.queue)} alternativas'
        )
