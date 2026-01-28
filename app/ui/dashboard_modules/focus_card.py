from PyQt5.QtWidgets import QFrame, QVBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import Qt

def _refresh_style(w):
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()

class FocusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("注意力监控")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.val_eye = QLabel("眼睛: 初始化...")
        self.val_eye.setObjectName("SubTitle")
        layout.addWidget(self.val_eye)

        self.val_distraction = QLabel("分心率: 0%")
        self.val_distraction.setObjectName("SubTitle")
        layout.addWidget(self.val_distraction)

        layout.addStretch()

        self.perclos_bar = QProgressBar()
        self.perclos_bar.setFixedHeight(22)
        self.perclos_bar.setTextVisible(True)
        self.perclos_bar.setAlignment(Qt.AlignCenter)
        self.perclos_bar.setFormat("疲劳值: %v")
        self.perclos_bar.setProperty("barLevel", "good")
        layout.addWidget(self.perclos_bar)

        self.score_bar = QProgressBar()
        self.score_bar.setFixedHeight(30)
        self.score_bar.setTextVisible(True)
        self.score_bar.setAlignment(Qt.AlignCenter)
        self.score_bar.setFormat("专注评分: %v")
        self.score_bar.setProperty("barLevel", "good")
        layout.addWidget(self.score_bar)

        _refresh_style(self.perclos_bar)
        _refresh_style(self.score_bar)

    def update_data(self, b_data):
        if not b_data:
            return

        # A. 疲劳值
        # 如果获取到 None，用 or 0.0 强制转为 0.0
        raw_perclos = float(b_data.get("perclos") or 0.0)
        perclos_val = int(raw_perclos * 100)
        self.perclos_bar.setValue(min(perclos_val, 100))
        self.perclos_bar.setFormat(f"疲劳值: {raw_perclos:.2f}")

        # >0.15 认为疲劳偏高
        self.perclos_bar.setProperty("barLevel", "bad" if raw_perclos > 0.15 else "good")
        _refresh_style(self.perclos_bar)

        # B. 专注分
        # 如果获取到 None，用 or 100 默认满分
        score = int(b_data.get("attention_score") or 100)
        self.score_bar.setValue(score)
        self.score_bar.setProperty("barLevel", "bad" if score < 60 else "good")
        _refresh_style(self.score_bar)

        # C. 眼睛状态
        state = b_data.get("blink_state", "no_face")
        if state == "open":
            eye_cn = "睁开"
        elif state == "closed":
            eye_cn = "闭合"
        elif state == "half":
            eye_cn = "半眯"
        else:
            eye_cn = "检测中"
        
        self.val_eye.setText(f"眼睛: {eye_cn}")

        # D. 分心率 
        r_away = float(b_data.get("away_ratio") or 0.0)
        r_down = float(b_data.get("down_ratio") or 0.0)
        r_gaze = float(b_data.get("gaze_ratio") or 0.0)
        
        # 取最大值显示
        max_dis = max(r_away, r_down, r_gaze)
        self.val_distraction.setText(f"分心率: {int(max_dis * 100)}%")