from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QCheckBox, QLabel, 
                             QSlider, QHBoxLayout, QGroupBox, QWidget)
from PyQt5.QtCore import Qt

class ControlsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 蓝色对号的 Base64 编码 (SVG)
        # 注意：这里我们只定义 Base64 字符串本身，不带 url() 外壳，方便后续处理
        icon_b64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIyMCA2IDkgMTcgNCAxMiIvPjwvc3ZnPg=="

        # 使用普通字符串 (不是 f-string)，避免 {} 冲突
        # 我们使用 REPLACE_ME 作为占位符
        style_sheet = """
            QFrame { 
                background: #ffffff; 
                border-radius: 8px; 
                border: 1px solid #e0e0e0; 
            }
            QGroupBox {
                font-weight: bold;
                border: none;
                border-top: 1px solid #eee;
                margin-top: 10px;
                padding-top: 10px;
                color: #007bff;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px;
            }
            
            /* 复选框整体 */
            QCheckBox { 
                color: #333; 
                font-size: 14px;
                padding: 8px 0; 
                border-bottom: 1px dashed #f0f0f0;
            }
            QCheckBox:hover {
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            
            /* --- 指示器（方框）默认样式 --- */
            QCheckBox::indicator { 
                width: 20px; 
                height: 20px;
                background: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:hover {
                border-color: #ced4da;
            }

            /* --- 选中状态：蓝色边框 + Base64图片 --- */
            QCheckBox::indicator:checked {
                background: #ffffff;
                border: 2px solid #007bff;
                image: url('REPLACE_ME');
            }
        """
        
        # 核心修复：使用 replace 注入 Base64 字符串
        self.setStyleSheet(style_sheet.replace("REPLACE_ME", icon_b64))
        
        self.setMinimumWidth(0)
        self.init_ui()

    def init_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(5)

        title = QLabel("监控参数设置")
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #333; border:none; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # === 1. 核心违规组 ===
        grp_core = QGroupBox("核心违规")
        lay_core = QVBoxLayout(grp_core)
        lay_core.setSpacing(0)
        lay_core.setContentsMargins(5, 10, 5, 5)
        
        self.chk_phone = self._create_row("玩手机")
        self.chk_away = self._create_row("离席检测")
        
        lay_core.addWidget(self.chk_phone)
        lay_core.addWidget(self.chk_away)
        layout.addWidget(grp_core)

        # === 2. 姿态与视力组 ===
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

        # === 3. 手部行为组 ===
        grp_hand = QGroupBox("手部行为")
        lay_hand = QVBoxLayout(grp_hand)
        lay_hand.setSpacing(0)
        lay_hand.setContentsMargins(5, 10, 5, 5)
        
        self.chk_chin = self._create_row("托腮")
        self.chk_face = self._create_row("摸脸")
        
        lay_hand.addWidget(self.chk_chin)
        lay_hand.addWidget(self.chk_face)
        layout.addWidget(grp_hand)

        # === 4. 音量控制 ===
        vol_box = QFrame()
        vol_box.setStyleSheet("border:none; border-top: 1px solid #eee; margin-top: 10px; padding-top:10px;")
        v_layout = QHBoxLayout(vol_box)
        v_layout.setContentsMargins(5, 0, 5, 0)
        
        lbl_vol = QLabel("提示音量")
        lbl_vol.setStyleSheet("font-size: 14px; color: #333;")
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.setFixedWidth(120)
        
        v_layout.addWidget(lbl_vol)
        v_layout.addStretch()
        v_layout.addWidget(self.slider_vol)
        layout.addWidget(vol_box)

        layout.addStretch()

    def _create_row(self, text):
        """创建单行控制项：文字在左，对号在右"""
        chk = QCheckBox(text)
        chk.setChecked(True)
        chk.setCursor(Qt.PointingHandCursor)
        
        # 核心设置：布局方向从右到左 -> [Label ... Checkbox]
        chk.setLayoutDirection(Qt.RightToLeft)
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
            "volume": self.slider_vol.value()
        }