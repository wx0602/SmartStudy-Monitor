from PyQt5.QtWidgets import QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen

class CyberLabel(QLabel):
    def __init__(self, text, size=10, color="#333333", bold=False, parent=None):
        super().__init__(text, parent)
        # 默认颜色为深灰
        weight = "bold" if bold else "normal"
        self.setStyleSheet(f"""
            color: {color}; 
            font-size: {size}pt; 
            font-weight: {weight};
            background: transparent;
        """)

class StatusLight(QFrame):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 30)
        
        self.label = QLabel(label_text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, 80, 30)
        # 初始状态：浅灰背景，深灰文字
        self.default_style = """
            background-color: #e9ecef; 
            color: #adb5bd; 
            border-radius: 4px; 
            border: 1px solid #dee2e6;
            font-weight: normal;
        """
        # 激活状态：红色背景，白色文字 (警示色)
        self.active_style = """
            background-color: #dc3545; 
            color: white; 
            border-radius: 4px; 
            border: 1px solid #dc3545;
            font-weight: bold;
        """
        self.setStyleSheet(self.default_style)

    def set_status(self, is_active):
        if is_active:
            self.setStyleSheet(self.active_style)
        else:
            self.setStyleSheet(self.default_style)

class GazeRadar(QFrame):
    """简易视线指示器 (浅色版)"""
    def __init__(self, size=80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.gx = 0
        self.gy = 0
        self.setStyleSheet("background: transparent;")

    def update_gaze(self, x, y, is_face_detected):
        self.gx = x
        self.gy = y
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # 1. 绘制背景圆盘 (浅灰边框，白色填充)
        painter.setPen(QPen(QColor("#dee2e6"), 2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(2, 2, w-4, h-4)
        
        # 2. 绘制十字准星 (浅灰)
        painter.setPen(QPen(QColor("#e9ecef"), 1))
        painter.drawLine(w//2, 4, w//2, h-4)
        painter.drawLine(4, h//2, w-4, h//2)

        # 3. 绘制视线点 (标准蓝)
        center_x = w/2 + self.gx * (w/2.5)
        center_y = h/2 + self.gy * (h/2.5)
        
        painter.setBrush(QColor("#007bff")) # 蓝色
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x)-4, int(center_y)-4, 8, 8)