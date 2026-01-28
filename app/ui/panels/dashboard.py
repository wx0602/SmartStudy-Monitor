from PyQt5.QtWidgets import QWidget, QHBoxLayout

from app.ui.dashboard_modules.focus_card import FocusCard
from app.ui.dashboard_modules.posture_card import PostureCard
from app.ui.dashboard_modules.behavior_card import BehaviorCard

#主要用于控制横向模块
class HorizontalMonitorBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(15) # 模块之间的间距

        # 实例化三个模块
        self.card_focus = FocusCard()
        self.card_posture = PostureCard()
        self.card_behavior = BehaviorCard()

        # 添加到布局，stretch 全部设为 1，保证宽度均等
        self.main_layout.addWidget(self.card_focus, stretch=1)
        self.main_layout.addWidget(self.card_posture, stretch=1)
        self.main_layout.addWidget(self.card_behavior, stretch=1)

    def update_data(self, a, b, c):
        # 将数据分发给各个子模块
        self.card_focus.update_data(b)      # B数据 专注模块
        self.card_posture.update_data(a)    # A数据 坐姿模块
        self.card_behavior.update_data(c)   # C数据 行为模块