import os
import re
import tempfile
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication

from dictionary import chain_candidates, english, spanish
from ocr import read_text
from platform_utils import type_text
from used_words import add_used


def extract_detected_word(text):
    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text or "")
    if not words:
        return ""
    return max(words, key=len).lower()


def normalize_region(region):
    if not isinstance(region, dict):
        return None
    required = ("x", "y", "width", "height")
    if not all(key in region for key in required):
        return None
    if int(region["width"]) < 5 or int(region["height"]) < 5:
        return None
    return {key: int(region[key]) for key in required}


class AutomaticChainEngine(QObject):
    status_changed = pyqtSignal(str)
    word_detected = pyqtSignal(str)
    reply_sent = pyqtSignal(str)
    exhausted = pyqtSignal(str)

    def __init__(self, settings, target=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.target = target
        self.region = normalize_region(settings.get("auto_region"))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.active = False
        self.busy = False
        self.source_word = ""
        self.queue = []
        self.last_reply = ""
        self.sent_at = 0.0
        self.waiting_for_change = False
        self.stable_candidate = ""
        self.stable_count = 0

    def update_settings(self, settings):
        self.settings = settings
        self.region = normalize_region(settings.get("auto_region"))
        if self.active:
            self.timer.setInterval(int(settings.get("auto_interval_ms", 700)))

    def set_target(self, target):
        self.target = target

    def start(self):
        if not self.region:
            raise ValueError("Selecciona primero la región que contiene la palabra del oponente.")

        self.active = True
        self.timer.start(max(300, int(self.settings.get("auto_interval_ms", 700))))
        self.status_changed.emit("Modo automático activo")

    def stop(self):
        self.active = False
        self.timer.stop()
        self.busy = False
        self.source_word = ""
        self.queue = []
        self.waiting_for_change = False
        self.status_changed.emit("Modo automático detenido")

    def capture_region(self):
        region = self.region
        center_x = region["x"] + region["width"] // 2
        center_y = region["y"] + region["height"] // 2

        from PyQt6.QtCore import QPoint

        screen = QGuiApplication.screenAt(QPoint(center_x, center_y))
        if screen is None:
            screen = QGuiApplication.primaryScreen()

        geometry = screen.geometry()
        local_x = region["x"] - geometry.x()
        local_y = region["y"] - geometry.y()

        pixmap = screen.grabWindow(
            0,
            local_x,
            local_y,
            region["width"],
            region["height"],
        )

        path = os.path.join(tempfile.gettempdir(), "wordhelper_auto_capture.png")
        if not pixmap.save(path, "PNG"):
            return None
        return path

    def tick(self):
        if not self.active or self.busy:
            return

        self.busy = True
        try:
            capture = self.capture_region()
            if not capture:
                return

            detected = extract_detected_word(read_text(capture))
            if not detected:
                self.stable_candidate = ""
                self.stable_count = 0
                return

            if detected == self.stable_candidate:
                self.stable_count += 1
            else:
                self.stable_candidate = detected
                self.stable_count = 1

            # Require the same OCR result twice to reduce accidental triggers.
            if self.stable_count < 2:
                return

            self.word_detected.emit(detected)
            self.handle_detected_word(detected)
        except Exception as exc:
            self.status_changed.emit(f"Auto: {exc}")
        finally:
            self.busy = False

    def handle_detected_word(self, detected):
        now = time.monotonic()

        if self.waiting_for_change:
            if detected != self.source_word:
                self.waiting_for_change = False
                self.source_word = ""
                self.queue = []
                self.last_reply = ""
                self.status_changed.emit(f"Cambio detectado: {detected}")
            else:
                retry_ms = int(self.settings.get("auto_retry_ms", 1800))
                if (now - self.sent_at) * 1000 >= retry_ms:
                    self.send_next()
                return

        if detected == self.source_word:
            return

        self.begin_turn(detected)

    def begin_turn(self, opponent_word):
        self.source_word = opponent_word.lower()
        add_used(self.source_word)

        suffix_length = max(1, int(self.settings.get("chain_letters", 2)))
        suffix = self.source_word[-suffix_length:]

        language = self.settings.get("auto_language", self.settings.get("language", "english"))
        dictionaries = []
        if language in ("english", "both"):
            dictionaries.append(english)
        if language in ("spanish", "both"):
            dictionaries.append(spanish)

        difficulty = self.settings.get("difficulty", "normal")
        candidates = []
        seen = set()

        for words in dictionaries:
            for word in chain_candidates(
                suffix,
                words,
                difficulty=difficulty,
                limit=80,
                min_length=int(self.settings.get("min_length", 1)),
                max_length=int(self.settings.get("max_length", 32)),
                smart_antirepeat=bool(self.settings.get("smart_antirepeat", True)),
            ):
                key = word.lower()
                if key not in seen and key != self.source_word:
                    candidates.append(word)
                    seen.add(key)

        if not candidates and self.settings.get("auto_fallback_suffix", True) and suffix_length > 1:
            fallback = self.source_word[-1:]
            for words in dictionaries:
                for word in chain_candidates(
                    fallback,
                    words,
                    difficulty=difficulty,
                    limit=80,
                    min_length=int(self.settings.get("min_length", 1)),
                    max_length=int(self.settings.get("max_length", 32)),
                    smart_antirepeat=bool(self.settings.get("smart_antirepeat", True)),
                ):
                    key = word.lower()
                    if key not in seen and key != self.source_word:
                        candidates.append(word)
                        seen.add(key)

        self.queue = candidates
        self.status_changed.emit(
            f"{self.source_word} → {suffix.upper()} · {len(self.queue)} respuestas"
        )

        if not self.queue:
            self.exhausted.emit(self.source_word)
            return

        self.send_next()

    def send_next(self):
        if not self.queue:
            self.exhausted.emit(self.source_word)
            self.waiting_for_change = False
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
        self.waiting_for_change = True
        self.reply_sent.emit(word)
        self.status_changed.emit(
            f'Probando "{word}" · {len(self.queue)} alternativas restantes'
        )
