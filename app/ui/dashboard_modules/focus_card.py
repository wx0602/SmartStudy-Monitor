from PyQt5.QtWidgets import QFrame, QVBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import Qt
from app.ui.common import CyberLabel

class FocusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 卡片背景样式
        self.setStyleSheet("""
            QFrame {
                background: #ffffff; 
                border-radius: 8px; 
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 1. 眼睛状态 (文字)
        self.val_eye = CyberLabel("眼睛: 睁开", 13, "#28a745")
        layout.addWidget(self.val_eye)

        # 2. 分心率 (文字)
        self.val_distraction = CyberLabel("分心率: 0%", 13, "#dc3545")
        layout.addWidget(self.val_distraction)
        
        # 弹簧: 把文字顶上去，进度条压到底
        layout.addStretch()

        # 3. 疲劳值进度条 (细)
        self.perclos_bar = QProgressBar()
        self.perclos_bar.setFixedHeight(22)
        self.perclos_bar.setTextVisible(True)
        self.perclos_bar.setAlignment(Qt.AlignCenter)
        self.perclos_bar.setFormat("疲劳值: %v") 
        layout.addWidget(self.perclos_bar)

        # 4. 专注分进度条 (粗)
        self.score_bar = QProgressBar()
        self.score_bar.setFixedHeight(30)
        self.score_bar.setTextVisible(True) 
        self.score_bar.setAlignment(Qt.AlignCenter)
        self.score_bar.setFormat("专注评分: %v")
        layout.addWidget(self.score_bar)

        # 初始化颜色 (绿 / 蓝)
        self.set_bar_style(self.perclos_bar, "#28a745") 
        self.set_bar_style(self.score_bar, "#007bff")

    def set_bar_style(self, bar, color):
        """设置进度条样式，文字强制为黑色"""
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: #e9ecef; 
                border: none; 
                border-radius: 6px;
                color: #000000; /* 核心修改：文字改为黑色 */
                font-weight: bold;
                font-size: 12px;
                text-align: center;
            }} 
            QProgressBar::chunk {{
                background: {color};
                border-radius: 6px;
            }}
        """)

    def update_data(self, b_data):
        """更新数据"""
        # --- A. 疲劳值 (越低越好 -> 绿) ---
        raw_perclos = b_data.get('perclos', 0.0)
        # 显示逻辑：放大100倍显示在进度条
        perclos_val = int(raw_perclos * 100)
        self.perclos_bar.setValue(min(perclos_val, 100))
        
        # 这里的 Hack：进度条 value 是整数(如15)，但文字显示原始小数(如0.15)
        # 我们直接用 setFormat 覆盖显示的文字
        self.perclos_bar.setFormat(f"疲劳值: {raw_perclos:.2f}")

        # 变色：> 0.15 变红(累)，否则绿(正常)
        if raw_perclos > 0.15:
            self.set_bar_style(self.perclos_bar, "#dc3545") 
        else:
            self.set_bar_style(self.perclos_bar, "#28a745")

        # --- B. 专注分 (越高越好 -> 蓝) ---
        score = int(b_data.get("attention_score", 100))
        self.score_bar.setValue(score)
        
        # 变色：< 60 变红(分心)，否则蓝(专注)
        if score < 60:
            self.set_bar_style(self.score_bar, "#dc3545")
        else:
            self.set_bar_style(self.score_bar, "#007bff")

        # --- C. 文字参数 ---
        eye_cn = "睁开" if b_data.get('blink_state', 'open') == "open" else "闭合"
        eye_color = "#28a745" if eye_cn == "睁开" else "#dc3545"
        self.val_eye.setText(f"眼睛: {eye_cn}")
        self.val_eye.setStyleSheet(f"color: {eye_color}; font-size: 13pt; background: transparent;")
        
        self.val_distraction.setText(f"分心率: {int(b_data.get('distraction_rate', 0)*100)}%")