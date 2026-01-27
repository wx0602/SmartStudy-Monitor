# app/ui/bubble.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (
    Qt, QRect, QPoint,
    QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, QPauseAnimation,
    pyqtSignal, pyqtProperty
)
from PyQt5.QtGui import (
    QColor, QPainter, QPainterPath, QFont, QFontDatabase
)
from PyQt5.QtCore import QRectF


class ToastBubble(QWidget):
    """
    Type1（轻度）：中心淡入 -> 停留 -> 淡出（不移动、不缩放、不闪）
    - light：半透明浅蓝
    - dark ：半透明深蓝
    ✅ 不使用任何 QGraphicsEffect（避免 QPainter 冲突）
    ✅ 可重复触发：show_toast 会强制 stop + 重播
    """
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._theme = "light"
        self._w, self._h = 380, 76
        self._radius = 999  # 椭圆
        self._alpha = 0.0   # 0~1 自己控制透明度
        self._text = ""

        self.setFixedSize(self._w, self._h)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._seq = QSequentialAnimationGroup(self)
        self._seq.finished.connect(self._on_finished)

        self.hide()

    # -------- alpha property (for animation) --------
    def getAlpha(self) -> float:
        return float(self._alpha)

    def setAlpha(self, v: float):
        self._alpha = max(0.0, min(1.0, float(v)))
        self.update()

    alpha = pyqtProperty(float, fget=getAlpha, fset=setAlpha)

    # -------- font (prettier) --------
    def _pick_font(self, pt: int, bold: bool = True) -> QFont:
        candidates = [
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "Segoe UI",
            "PingFang SC",
            "Noto Sans CJK SC",
        ]
        families = set(QFontDatabase().families())
        fam = next((f for f in candidates if f in families), "Microsoft YaHei")

        f = QFont(fam)
        f.setPointSize(pt)
        f.setBold(bold)
        f.setHintingPreference(QFont.PreferFullHinting)
        return f

    # -------- theme / palette --------
    def set_theme(self, theme: str):
        self._theme = theme or "light"
        self.update()

    def _palette(self):
        # 低饱和：浅蓝 / 深蓝
        if self._theme == "dark":
            return dict(
                bg=QColor(18, 38, 78, 205),     # 深蓝玻璃
                bd=QColor(150, 205, 255, 70),
                fg=QColor(255, 255, 255, 242),
                shadow=QColor(0, 0, 0, 140),
            )
        return dict(
            bg=QColor(220, 244, 255, 230),    # 浅蓝玻璃
            bd=QColor(120, 180, 255, 150),
            fg=QColor(18, 32, 50, 240),
            shadow=QColor(0, 0, 0, 90),
        )

    # -------- geometry --------
    def _parent_rect(self):
        p = self.parentWidget()
        return p.rect() if p else QRect(0, 0, 800, 600)

    def _center_rect(self):
        pr = self._parent_rect()
        x = (pr.width() - self._w) // 2
        y = (pr.height() - self._h) // 2
        return QRect(max(0, x), max(0, y), self._w, self._h)

    # -------- API --------
    def show_toast(self, text: str, duration_ms: int = 1200):
        # ✅ 可重复触发：正在播就先停掉并重置
        if self._seq.state() != 0:
            self._seq.stop()

        self._text = text
        self.setGeometry(self._center_rect())

        self.setAlpha(0.0)
        self.show()
        self.raise_()

        fade_in = QPropertyAnimation(self, b"alpha")
        fade_in.setDuration(220)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)

        pause = QPauseAnimation(max(0, int(duration_ms)))

        fade_out = QPropertyAnimation(self, b"alpha")
        fade_out.setDuration(280)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)

        self._seq.clear()
        self._seq.addAnimation(fade_in)
        self._seq.addAnimation(pause)
        self._seq.addAnimation(fade_out)
        self._seq.start()

    def _on_finished(self):
        self.hide()
        self.finished.emit()

    # -------- paint --------
    def paintEvent(self, event):
        if self._alpha <= 0.001:
            return

        pal = self._palette()

        def with_alpha(c: QColor, a_mul: float):
            c2 = QColor(c)
            c2.setAlpha(int(c.alpha() * a_mul))
            return c2

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect())
        body_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)

        # ✅ 伪阴影（多层、下偏移，避免 QGraphicsEffect）
        shadow = pal["shadow"]
        for i in range(10):
            a = (10 - i) / 10.0
            r = body_rect.adjusted(2 + i, 8 + i, -(2 + i), -(8 + i))
            path = QPainterPath()
            path.addRoundedRect(r, self._radius, self._radius)
            p.setPen(Qt.NoPen)
            p.setBrush(with_alpha(shadow, self._alpha * 0.10 * a))
            p.drawPath(path)

        # ✅ 主体
        path = QPainterPath()
        path.addRoundedRect(body_rect, self._radius, self._radius)
        p.setBrush(with_alpha(pal["bg"], self._alpha))
        p.setPen(with_alpha(pal["bd"], self._alpha))
        p.drawPath(path)

        # ✅ 文本：更漂亮（字体 + 微阴影）
        text_rect = rect.adjusted(26, 12, -26, -12)
        font = self._pick_font(pt=15, bold=True)
        p.setFont(font)

        # 微阴影（提升质感）
        shadow_text = QColor(pal["fg"])
        shadow_text.setAlpha(int(45 * self._alpha))
        p.setPen(shadow_text)
        p.drawText(text_rect.translated(0, 1), Qt.AlignCenter | Qt.TextWordWrap, self._text)

        p.setPen(with_alpha(pal["fg"], self._alpha))
        p.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self._text)

        p.end()


class ModalBubble(QWidget):
    """
    Type2（重度）：顶层弹窗（Qt.Tool），必须手动关闭，不自动消失
    - show_at(text, global_rect): 居中到 video_frame 的全局矩形
    ✅ 不使用任何 QGraphicsEffect（避免 QPainter 冲突）
    ✅ 可重复触发：show_at 每次都会淡入到 1
    """
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._theme = "light"
        self._w, self._h = 520, 180
        self._radius = 22
        self._alpha = 0.0
        self._text = ""
        self._closing = False

        self.setFixedSize(self._w, self._h)

        # 手绘关闭按钮区域
        self._close_rect = QRect(self._w - 44, 14, 30, 30)

        self._anim_in = None
        self._anim_out = None

        self.hide()

    # -------- alpha property --------
    def getAlpha(self) -> float:
        return float(self._alpha)

    def setAlpha(self, v: float):
        self._alpha = max(0.0, min(1.0, float(v)))
        self.update()

    alpha = pyqtProperty(float, fget=getAlpha, fset=setAlpha)

    # -------- font --------
    def _pick_font(self, pt: int, bold: bool = True) -> QFont:
        candidates = [
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "Segoe UI",
            "PingFang SC",
            "Noto Sans CJK SC",
        ]
        families = set(QFontDatabase().families())
        fam = next((f for f in candidates if f in families), "Microsoft YaHei")

        f = QFont(fam)
        f.setPointSize(pt)
        f.setBold(bold)
        f.setHintingPreference(QFont.PreferFullHinting)
        return f

    # -------- theme / palette --------
    def set_theme(self, theme: str):
        self._theme = theme or "light"
        self.update()

    def _palette(self):
        # 低饱和：浅红 / 深红
        if self._theme == "dark":
            return dict(
                bg=QColor(92, 24, 36, 215),       # 深红玻璃
                bd=QColor(255, 150, 175, 90),
                fg=QColor(255, 255, 255, 242),
                shadow=QColor(0, 0, 0, 170),
                close_bg=QColor(255, 255, 255, 28),
                close_fg=QColor(255, 255, 255, 235),
            )
        return dict(
            bg=QColor(255, 236, 242, 235),      # 浅红玻璃
            bd=QColor(235, 130, 150, 160),
            fg=QColor(45, 18, 26, 240),
            shadow=QColor(0, 0, 0, 115),
            close_bg=QColor(0, 0, 0, 18),
            close_fg=QColor(45, 18, 26, 220),
        )

    # -------- API --------
    def show_at(self, text: str, target_global_rect: QRect):
        self._text = text
        self._closing = False

        cx = target_global_rect.x() + target_global_rect.width() // 2
        cy = target_global_rect.y() + target_global_rect.height() // 2
        x = cx - self._w // 2
        y = cy - self._h // 2
        self.move(QPoint(x, y))

        if not self.isVisible():
            self.setAlpha(0.0)
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            # 可见时更新位置/文本，也要置顶
            self.raise_()
            self.activateWindow()

        # 每次 show_at 都保证淡入到 1（可重复触发不会“只显示一次”）
        if self._anim_out and self._anim_out.state() != 0:
            self._anim_out.stop()

        if self._anim_in and self._anim_in.state() != 0:
            self._anim_in.stop()

        self._anim_in = QPropertyAnimation(self, b"alpha")
        self._anim_in.setDuration(220)
        self._anim_in.setStartValue(self.alpha)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_in.start()

    def close_modal(self):
        if self._closing:
            return
        self._closing = True

        if self._anim_in and self._anim_in.state() != 0:
            self._anim_in.stop()

        self._anim_out = QPropertyAnimation(self, b"alpha")
        self._anim_out.setDuration(200)
        self._anim_out.setStartValue(self.alpha)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)

        def _after():
            self.hide()
            self._closing = False
            self.closed.emit()

        self._anim_out.finished.connect(_after)
        self._anim_out.start()

    # -------- interaction --------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._close_rect.contains(e.pos()):
            self.close_modal()
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._close_rect.contains(e.pos()):
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(e)

    # -------- paint --------
    def paintEvent(self, event):
        if self._alpha <= 0.001:
            return

        pal = self._palette()

        def with_alpha(c: QColor, a_mul: float):
            c2 = QColor(c)
            c2.setAlpha(int(c.alpha() * a_mul))
            return c2

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect())
        body_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)

        # 伪阴影（多层）
        shadow = pal["shadow"]
        for i in range(12):
            a = (12 - i) / 12.0
            r = body_rect.adjusted(3 + i, 10 + i, -(3 + i), -(10 + i))
            path = QPainterPath()
            path.addRoundedRect(r, self._radius, self._radius)
            p.setPen(Qt.NoPen)
            p.setBrush(with_alpha(shadow, self._alpha * 0.10 * a))
            p.drawPath(path)

        # 主体
        path = QPainterPath()
        path.addRoundedRect(body_rect, self._radius, self._radius)
        p.setBrush(with_alpha(pal["bg"], self._alpha))
        p.setPen(with_alpha(pal["bd"], self._alpha))
        p.drawPath(path)

        # 关闭按钮（手绘）
        cr = QRectF(self._close_rect)
        btn_path = QPainterPath()
        btn_path.addRoundedRect(cr, 10, 10)
        p.setPen(Qt.NoPen)
        p.setBrush(with_alpha(pal["close_bg"], self._alpha))
        p.drawPath(btn_path)

        p.setPen(with_alpha(pal["close_fg"], self._alpha))
        p.setFont(self._pick_font(pt=12, bold=True))
        p.drawText(cr, Qt.AlignCenter, "✕")

        # 文本（更权威 + 微阴影）
        text_rect = rect.adjusted(32, 46, -32, -36)
        p.setFont(self._pick_font(pt=18, bold=True))

        shadow_text = QColor(pal["fg"])
        shadow_text.setAlpha(int(55 * self._alpha))
        p.setPen(shadow_text)
        p.drawText(text_rect.translated(0, 1), Qt.AlignCenter | Qt.TextWordWrap, self._text)

        p.setPen(with_alpha(pal["fg"], self._alpha))
        p.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self._text)

        p.end()
