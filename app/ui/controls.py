from PyQt5.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
                             QCheckBox, QSlider, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ControlsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; color: #e0e0e0;")
        
        # 1. 主布局 (绑定在 self 上)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        
        # 标题
        title = QLabel("系统控制终端")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #888; margin-bottom: 10px;")
        self.main_layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea {background: transparent;} QScrollBar:vertical {width:6px; background:transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        
        # 2. 内容布局 (绑定在 content 上) -> 关键修改：改名为 content_layout
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(15, 0, 15, 20)
        self.content_layout.setSpacing(15)
        
        self.switches = {}

        # 模块 A
        self.create_group("🚫 严重干扰拦截", [
            ("phone", "玩手机检测", True),
            ("hunch", "严重驼背检测", True),
            ("sleep", "闭眼/瞌睡检测", True)
        ])
        
        # 模块 B
        self.create_group("🦴 体态与行为纠正", [
            ("posture", "坐姿侧倾/歪头", True),
            ("turtle",  "脖子前伸 (乌龟颈)", True),
            ("hands",   "托腮/摸脸习惯", False),
            ("gaze",    "视线偏离屏幕", True)
        ])
        
        self.content_layout.addStretch()
        
        # 模块 C: 底部音量控制
        self.create_volume_control()
        
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def create_group(self, title, items):
        group = QFrame()
        group.setStyleSheet("background: #252525; border-radius: 8px; border: 1px solid #333;")
        vbox = QVBoxLayout(group)
        vbox.setContentsMargins(15, 15, 15, 15)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        lbl_title.setStyleSheet("color: #aaa; padding-bottom: 5px; border-bottom: 1px solid #444; margin-bottom: 5px;")
        vbox.addWidget(lbl_title)
        
        for key, text, default in items:
            cb = QCheckBox(text)
            cb.setChecked(default)
            cb.setCursor(Qt.PointingHandCursor)
            self.switches[key] = cb
            vbox.addWidget(cb)
            
        # 使用新名字 content_layout
        self.content_layout.addWidget(group)

    def create_volume_control(self):
        frame = QFrame()
        frame.setStyleSheet("background: #1a1a1a; border-top: 1px solid #333;")
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(20, 15, 20, 15)
        
        row_label = QHBoxLayout()
        row_label.addWidget(QLabel("🔊 提示音量"))
        self.lbl_vol_val = QLabel("80%")
        self.lbl_vol_val.setAlignment(Qt.AlignRight)
        self.lbl_vol_val.setStyleSheet("color: #00e5ff; font-weight: bold;")
        row_label.addWidget(self.lbl_vol_val)
        vbox.addLayout(row_label)
        
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_val.setText(f"{v}%"))
        vbox.addWidget(self.slider_vol)
        
        # 这里直接加到 main_layout，不再调用 self.layout()
        self.main_layout.addWidget(frame)

    def get_config(self):
        config = {k: cb.isChecked() for k, cb in self.switches.items()}
        config["volume"] = self.slider_vol.value()
        return config