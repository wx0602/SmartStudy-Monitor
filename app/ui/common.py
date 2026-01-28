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
        # 激活状态：红色背景，白色文字
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