from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
import math

class CyberLabel(QLabel):
    def __init__(self, text, size=12, color="#00ff00", bold=False):
        super().__init__(text)
        weight = "bold" if bold else "normal"
        self.setStyleSheet(f"color: {color}; font-family: 'Microsoft YaHei'; font-size: {size}pt; font-weight: {weight};")

class GazeRadar(QWidget):
    def __init__(self, size=100):
        super().__init__()
        self.setFixedSize(size, size)
        self.gx = 0.0
        self.gy = 0.0
        self.active = False
    def update_gaze(self, gx, gy, active):
        self.gx = gx if gx is not None else 0.0
        self.gy = gy if gy is not None else 0.0
        self.active = active
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 5
        painter.setPen(QPen(QColor(0, 50, 0), 2))
        painter.setBrush(QBrush(QColor(0, 20, 0)))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor(0, 100, 0), 1))
        painter.drawLine(cx - radius, cy, cx + radius, cy)
        painter.drawLine(cx, cy - radius, cx, cy + radius)
        if self.active:
            dot_x = cx + int(self.gx * radius)
            dot_y = cy + int(self.gy * radius) 
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 255, 255)))
            painter.drawEllipse(dot_x - 4, dot_y - 4, 8, 8)

class StatusLight(QLabel):
    def __init__(self, text, on_color="#ff3333"):
        super().__init__(text)
        self.on_style = f"background-color: {on_color}; color: white; border-radius: 5px; padding: 4px;"
        self.off_style = "background-color: #333; color: #777; border-radius: 5px; padding: 4px;"
        self.setStyleSheet(self.off_style)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Microsoft YaHei", 10))
    def set_status(self, is_on):
        self.setStyleSheet(self.on_style if is_on else self.off_style)