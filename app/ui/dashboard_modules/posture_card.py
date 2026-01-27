from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel
from PyQt5.QtCore import Qt

def _refresh_style(w):
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()

class PostureCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)

        title = QLabel("姿态监控")
        title.setObjectName("Title")
        layout.addWidget(title, 0, 0, 1, 2)

        self.posture_status = QLabel("姿态标准")
        self.posture_status.setObjectName("PostureStatus")
        self.posture_status.setProperty("state", "good")
        self.posture_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        _refresh_style(self.posture_status)

        self.val_dist = QLabel("距离: 正常")
        self.val_dist.setObjectName("SubTitle")

        self.val_shoulder = QLabel("肩斜: 0.0°")
        self.val_shoulder.setObjectName("SubTitle")

        self.val_neck = QLabel("颈前: 0.0°")
        self.val_neck.setObjectName("SubTitle")

        layout.addWidget(self.posture_status, 1, 0, 1, 2)
        layout.addWidget(self.val_dist,       2, 0, 1, 2)
        layout.addWidget(self.val_shoulder,   3, 0)
        layout.addWidget(self.val_neck,       3, 1)

    def update_data(self, a_data):
        is_bad = bool(a_data.get("is_hunchback")) or bool(a_data.get("is_shoulder_tilted"))

        self.posture_status.setText("姿态异常" if is_bad else "姿态标准")
        self.posture_status.setProperty("state", "bad" if is_bad else "good")
        _refresh_style(self.posture_status)

        self.val_shoulder.setText(f"肩斜: {float(a_data.get('shoulder_tilt_angle', 0.0)):.1f}°")
        self.val_neck.setText(f"颈前: {float(a_data.get('neck_tilt', 0.0)):.1f}°")

        raw_dist = a_data.get("dist_screen", "normal")
        dist_map = {"normal": "正常", "too_close": "太近", "too_far": "太远"}
        dist_text = f"{raw_dist:.1f} cm" if isinstance(raw_dist, (int, float)) else dist_map.get(str(raw_dist), "正常")
        self.val_dist.setText(f"距离: {dist_text}")
