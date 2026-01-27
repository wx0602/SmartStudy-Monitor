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

        self.val_eye = QLabel("眼睛: 睁开")
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
        # A. 疲劳值
        raw_perclos = float(b_data.get("perclos", 0.0))
        perclos_val = int(raw_perclos * 100)
        self.perclos_bar.setValue(min(perclos_val, 100))
        self.perclos_bar.setFormat(f"疲劳值: {raw_perclos:.2f}")

        # >0.15 认为疲劳偏高
        self.perclos_bar.setProperty("barLevel", "bad" if raw_perclos > 0.15 else "good")
        _refresh_style(self.perclos_bar)

        # B. 专注分
        score = int(b_data.get("attention_score", 100))
        self.score_bar.setValue(score)
        self.score_bar.setProperty("barLevel", "bad" if score < 60 else "good")
        _refresh_style(self.score_bar)

        # C. 文字
        eye_cn = "睁开" if b_data.get("blink_state", "open") == "open" else "闭合"
        self.val_eye.setText(f"眼睛: {eye_cn}")

        dis = float(b_data.get("distraction_rate", 0.0))
        self.val_distraction.setText(f"分心率: {int(dis * 100)}%")
