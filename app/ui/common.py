from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush

# 发光文字标签
# 功能：创建一个带有特定颜色和字体的 QLabel，用于显示科幻风格的数值
class CyberLabel(QLabel):
    def __init__(self, text, size=12, color="#00ff00", bold=False):
        super().__init__(text)
        # 根据参数设置粗体
        weight = "bold" if bold else "normal"
        # 使用 QSS 设置样式：微软雅黑字体，指定颜色和大小
        self.setStyleSheet(f"color: {color}; font-family: 'Microsoft YaHei'; font-size: {size}pt; font-weight: {weight};")

# 状态指示灯
# 功能：模拟一个 LED 灯，有“亮”和“灭”两种状态，用于显示如“玩手机”等布尔状态
class StatusLight(QLabel):
    def __init__(self, text, on_color="#ff3333"):
        super().__init__(text)
        # 定义“亮”时的样式：背景色高亮，圆角
        self.on_style = f"background-color: {on_color}; color: white; border-radius: 5px; padding: 4px;"
        # 定义“灭”时的样式：深灰色背景，灰色文字
        self.off_style = "background-color: #333; color: #777; border-radius: 5px; padding: 4px;"
        
        self.setStyleSheet(self.off_style)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Microsoft YaHei", 10))

    # 切换灯的开关状态
    def set_status(self, is_on):
        self.setStyleSheet(self.on_style if is_on else self.off_style)

# 视线雷达
# 功能：自定义绘制的 Widget，像雷达一样显示眼球的视线落点
class GazeRadar(QWidget):
    def __init__(self, size=100):
        super().__init__()
        self.setFixedSize(size, size)
        self.gx = 0.0 # 视线 X 坐标 (-1 到 1)
        self.gy = 0.0 # 视线 Y 坐标 (-1 到 1)
        self.active = False # 是否有有效数据

    # 接收来自 AI 的视线数据并触发重绘
    def update_gaze(self, gx, gy, active):
        self.gx = gx if gx is not None else 0.0
        self.gy = gy if gy is not None else 0.0
        self.active = active
        self.update() # 触发 paintEvent

    # 核心绘制逻辑
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # 开启抗锯齿
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 5
        
        # 1. 画深绿色的背景圆
        painter.setPen(QPen(QColor(0, 50, 0), 2))
        painter.setBrush(QBrush(QColor(0, 20, 0)))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        # 2. 画十字准星
        painter.setPen(QPen(QColor(0, 100, 0), 1))
        painter.drawLine(cx - radius, cy, cx + radius, cy)
        painter.drawLine(cx, cy - radius, cx, cy + radius)
        
        # 3. 如果数据有效，画代表视线的亮青色圆点
        if self.active:
            # 将归一化坐标 (-1~1) 映射到像素坐标
            dot_x = cx + int(self.gx * radius)
            dot_y = cy + int(self.gy * radius) 
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 255, 255)))
            painter.drawEllipse(dot_x - 4, dot_y - 4, 8, 8)