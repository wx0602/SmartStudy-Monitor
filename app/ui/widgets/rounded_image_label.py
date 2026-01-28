from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath

#把显示的 pixmap 裁成圆角，为避免冲突选择在 paintEvent 内裁剪绘制
class RoundedImageLabel(QLabel):

    def __init__(self, radius: int = 18, parent=None):
        super().__init__(parent)
        self._radius = int(radius)
        self._raw_pixmap = None

        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)  # 缩放裁剪
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def setRadius(self, r: int):
        self._radius = int(r)
        self.update()

    def setPixmap(self, pm: QPixmap):
        # 只缓存原始图，不在这里做 QPainter + super().setPixmap(out)
        self._raw_pixmap = pm
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())

        # 圆角裁剪
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        p.setClipPath(path)

        if self._raw_pixmap and not self._raw_pixmap.isNull():
            # 等比放大填充
            scaled = self._raw_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            p.drawPixmap(-x, -y, scaled)
        else:
            # 没有画面时显示文字
            p.setClipping(False)
            p.drawText(self.rect(), Qt.AlignCenter, self.text())

        p.end()
