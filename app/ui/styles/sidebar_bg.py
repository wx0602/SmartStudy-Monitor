from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPixmap, QPainterPath
from PyQt5.QtCore import Qt, QRectF

# 横向部分背景
class SidebarBackgroundFrame(QFrame):
    def __init__(self, parent=None, radius=14):
        super().__init__(parent)
        self._pix = None
        self._radius = radius
        self.setAttribute(Qt.WA_StyledBackground, True)

    def set_bg_image(self, image_path: str):
        pix = QPixmap(image_path) if image_path else QPixmap()
        self._pix = pix if not pix.isNull() else None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self._pix:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 圆角裁剪
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        p.setClipPath(path)

        # 背景图铺满
        scaled = self._pix.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        p.drawPixmap(-x, -y, scaled)
