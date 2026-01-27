from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath


class RoundedImageLabel(QLabel):
    """把显示的 pixmap 裁成圆角（真正对画面生效）- 安全版：在 paintEvent 内裁剪绘制"""
    def __init__(self, radius: int = 18, parent=None):
        super().__init__(parent)
        self._radius = int(radius)
        self._raw_pixmap = None

        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)  # 我们自己缩放裁剪
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # ✅ 关键：避免 Qt 认为这是不透明控件而走一些优化路径
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def setRadius(self, r: int):
        self._radius = int(r)
        self.update()

    def setPixmap(self, pm: QPixmap):
        # ✅ 只缓存原始图，不在这里做 QPainter + super().setPixmap(out)
        self._raw_pixmap = pm
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update()

    def paintEvent(self, event):
        # ✅ 不调用 QLabel.paintEvent，避免它内部再画一次 pixmap 导致重入/冲突
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())

        # 圆角裁剪
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        p.setClipPath(path)

        if self._raw_pixmap and not self._raw_pixmap.isNull():
            # cover：等比放大填充
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
