from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

# 轻提示气泡
# 功能：在视频右下角显示一个圆形的、半透明的提示框，带有淡入淡出动画
class NotificationBubble(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True) # 允许文字自动换行
        
        # 样式：半透明橙色背景 + 白色半透明边框 + 圆形
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 170, 0, 220); 
                color: white; border-radius: 70px; padding: 10px;
                font-family: 'Microsoft YaHei'; font-size: 15px; font-weight: bold;
                border: 3px solid rgba(255, 255, 255, 180);
            }
        """)
        
        # 定时器：用于控制气泡显示多久后自动消失
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)
        
        # 动画特效：透明度动画 (Opacity)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300) # 动画时长 300ms
        self.hide()

    # 显示消息并播放淡入动画
    def show_message(self, text):
        self.setText(text)
        self.show(); self.raise_() # 确保浮在最上层
        
        # 淡入：透明度 0 -> 1
        self.anim.setStartValue(0.0); self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic); self.anim.start()
        
        # 启动计时器，3秒后执行 fade_out
        self.hide_timer.start(3000)

    # 播放淡出动画并隐藏
    def fade_out(self):
        # 淡出：透明度 1 -> 0
        self.anim.setStartValue(1.0); self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InCubic); self.anim.start()
        # 动画结束后彻底隐藏控件
        self.anim.finished.connect(self.hide)