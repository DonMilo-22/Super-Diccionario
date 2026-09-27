import os
import tempfile

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class CaptureOverlay(QWidget):
    captured = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.screen_geometry = self.screen.geometry()
        self.screenshot = self.screen.grabWindow(0)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(self.screen_geometry)

    def show_capture(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.selecting:
            return

        self.selecting = False
        self.end_point = event.position().toPoint()
        rect = QRect(self.start_point, self.end_point).normalized()

        if rect.width() < 5 or rect.height() < 5:
            self.cancel_capture()
            return

        capture_file = os.path.join(
            tempfile.gettempdir(),
            "wordhelper_capture.png",
        )

        cropped = self.screenshot.copy(rect)
        if not cropped.save(capture_file, "PNG"):
            self.cancel_capture()
            return

        self.hide()
        self.captured.emit(capture_file)
        self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_capture()

    def cancel_capture(self):
        self.hide()
        self.cancelled.emit()
        self.deleteLater()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.screenshot)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 115))

        if self.start_point != self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawPixmap(rect, self.screenshot, rect)
            painter.setPen(QPen(QColor(108, 99, 255), 2))
            painter.drawRect(rect)


class RegionSelector(QWidget):
    selected = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.screen_geometry = self.screen.geometry()
        self.screenshot = self.screen.grabWindow(0)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(self.screen_geometry)

    def show_selector(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.selecting:
            return

        self.selecting = False
        self.end_point = event.position().toPoint()
        rect = QRect(self.start_point, self.end_point).normalized()

        if rect.width() < 5 or rect.height() < 5:
            self.cancel_selection()
            return

        self.hide()
        self.selected.emit({
            "x": self.screen_geometry.x() + rect.x(),
            "y": self.screen_geometry.y() + rect.y(),
            "width": rect.width(),
            "height": rect.height(),
        })
        self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_selection()

    def cancel_selection(self):
        self.hide()
        self.cancelled.emit()
        self.deleteLater()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.screenshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 135))

        if self.start_point != self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawPixmap(rect, self.screenshot, rect)
            painter.setPen(QPen(QColor(255, 92, 168), 2))
            painter.drawRect(rect)
