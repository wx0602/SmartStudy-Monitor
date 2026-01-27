from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap, QColor
from PyQt5.QtCore import Qt

class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_color = QColor("#000000")  # 改成 QColor
        self._bg_pix = None

    def set_background(self, color: str, image_path: str):
        # color 允许传 "#RRGGBB" 或 QColor
        self._bg_color = QColor(color) if not isinstance(color, QColor) else color

        pix = QPixmap(image_path) if image_path else QPixmap()
        self._bg_pix = pix if not pix.isNull() else None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self._bg_color)  # 这里就不会报错了

        if self._bg_pix:
            scaled = self._bg_pix.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            p.drawPixmap(-x, -y, scaled)