from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QCheckBox, QLabel,
    QSlider, QHBoxLayout, QGroupBox
)
from PyQt5.QtCore import Qt


class ControlsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 由主题系统确定的卡片外观
        self.setObjectName("Card")
        self.setMinimumWidth(0)

        icon_b64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIyMCA2IDkgMTcgNCAxMiIvPjwvc3ZnPg=="

        # 保留 indicator 的 image 注入
        self.setStyleSheet(f"""
            QCheckBox::indicator:checked {{
                image: url('{icon_b64}');
            }}
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 15)
        layout.setSpacing(8)

        title = QLabel("监控参数设置")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 1. 核心违规组
        grp_core = QGroupBox("核心违规")
        lay_core = QVBoxLayout(grp_core)
        lay_core.setSpacing(0)
        lay_core.setContentsMargins(5, 10, 5, 5)

        self.chk_phone = self._create_row("玩手机")
        self.chk_away = self._create_row("离席检测")
        lay_core.addWidget(self.chk_phone)
        lay_core.addWidget(self.chk_away)
        layout.addWidget(grp_core)

        # 2. 姿态与视力组
        grp_body = QGroupBox("姿态与视力")
        lay_body = QVBoxLayout(grp_body)
        lay_body.setSpacing(0)
        lay_body.setContentsMargins(5, 10, 5, 5)

        self.chk_sleep = self._create_row("闭眼/睡觉")
        self.chk_posture = self._create_row("坐姿/脖子")
        self.chk_dist = self._create_row("距离过近")
        lay_body.addWidget(self.chk_sleep)
        lay_body.addWidget(self.chk_posture)
        lay_body.addWidget(self.chk_dist)
        layout.addWidget(grp_body)

        # 3. 手部行为组
        grp_hand = QGroupBox("手部行为")
        lay_hand = QVBoxLayout(grp_hand)
        lay_hand.setSpacing(0)
        lay_hand.setContentsMargins(5, 10, 5, 5)

        self.chk_chin = self._create_row("托腮")
        self.chk_face = self._create_row("摸脸")
        lay_hand.addWidget(self.chk_chin)
        lay_hand.addWidget(self.chk_face)
        layout.addWidget(grp_hand)

        # 4. 音量控制
        vol_box = QFrame()
        vol_box.setObjectName("Container") 
        v_layout = QHBoxLayout(vol_box)
        v_layout.setContentsMargins(10, 10, 10, 10)

        lbl_vol = QLabel("提示音量")
        lbl_vol.setObjectName("SubTitle")
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.setFixedWidth(140)

        v_layout.addWidget(lbl_vol)
        v_layout.addStretch()
        v_layout.addWidget(self.slider_vol)
        layout.addWidget(vol_box)

        layout.addStretch()

    def _create_row(self, text):
        chk = QCheckBox(text)
        chk.setChecked(True)
        chk.setCursor(Qt.PointingHandCursor)
        chk.setLayoutDirection(Qt.RightToLeft)  # 文字左，对号右
        return chk

    def get_config(self):
        return {
            "phone": self.chk_phone.isChecked(),
            "away": self.chk_away.isChecked(),
            "sleep": self.chk_sleep.isChecked(),
            "posture": self.chk_posture.isChecked(),
            "dist": self.chk_dist.isChecked(),
            "chin": self.chk_chin.isChecked(),
            "face": self.chk_face.isChecked(),
            "volume": self.slider_vol.value(),
        }
