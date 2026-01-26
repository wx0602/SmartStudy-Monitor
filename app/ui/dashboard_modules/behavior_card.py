from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt

class BehaviorLabel(QLabel):
    """
    无表情纯文字版状态块
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        
        # 允许自动拉伸填充
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 1. 未触发样式 (淡灰底 + 黑字 + 16px)
        self.inactive_style = """
            QLabel {
                background-color: #f8f9fa;
                color: #000000;          
                border-radius: 8px;
                font-size: 16px;         /* 字体增大，提升可读性 */
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
        """
        
        # 2. 触发样式 (警示黄底 + 黑字 + 18px特粗)
        self.active_style = """
            QLabel {
                background-color: #ffc107; 
                color: #000000;            
                border-radius: 8px;
                font-size: 18px;           /* 报警时字体更大，更显眼 */
                font-weight: 900;          /* 特粗 */
                border: 2px solid #e0a800;
            }
        """
        self.setStyleSheet(self.inactive_style)

    def set_status(self, is_active):
        """切换状态"""
        if is_active:
            self.setStyleSheet(self.active_style)
        else:
            self.setStyleSheet(self.inactive_style)


class BehaviorCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 容器背景
        self.setStyleSheet("""
            QFrame {
                background: #ffffff; 
                border-radius: 8px; 
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 实例化标签 (去掉 Emoji，仅保留中文)
        self.light_phone = BehaviorLabel("玩手机")
        self.light_chin = BehaviorLabel("托腮")
        self.light_face = BehaviorLabel("摸脸")
        self.light_away = BehaviorLabel("离席")
        
        # 2x2 布局
        layout.addWidget(self.light_phone, 0, 0)
        layout.addWidget(self.light_chin, 0, 1)
        layout.addWidget(self.light_face, 1, 0)
        layout.addWidget(self.light_away, 1, 1)

    def update_data(self, c_data):
        """数据更新逻辑"""
        # 1. 手机
        self.light_phone.set_status(c_data.get("手机使用", {}).get("使用手机", False))
        
        # 2. 手部
        h = c_data.get("手部行为", {})
        self.light_chin.set_status(h.get("托腮", False))
        self.light_face.set_status(h.get("频繁摸脸", False))
        
        # 3. 离席
        self.light_away.set_status(c_data.get("离席检测", {}).get("离席", False))