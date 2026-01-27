from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt

def _refresh_style(w):
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()

class BehaviorLabel(QLabel):
    """纯文字状态块：样式由主题 QSS 统一控制"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setObjectName("StateInactive")

    def set_status(self, is_active: bool):
        self.setObjectName("StateActive" if is_active else "StateInactive")
        _refresh_style(self)

class BehaviorCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        self.light_phone = BehaviorLabel("玩手机")
        self.light_chin  = BehaviorLabel("托腮")
        self.light_face  = BehaviorLabel("摸脸")
        self.light_away  = BehaviorLabel("离席")

        layout.addWidget(self.light_phone, 0, 0)
        layout.addWidget(self.light_chin,  0, 1)
        layout.addWidget(self.light_face,  1, 0)
        layout.addWidget(self.light_away,  1, 1)

    def update_data(self, c_data):
        self.light_phone.set_status(bool(c_data.get("手机使用", {}).get("使用手机", False)))

        h = c_data.get("手部行为", {})
        self.light_chin.set_status(bool(h.get("托腮", False)))
        self.light_face.set_status(bool(h.get("频繁摸脸", False)))

        self.light_away.set_status(bool(c_data.get("离席检测", {}).get("离席", False)))
