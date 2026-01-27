from PyQt5.QtWidgets import QFrame, QGridLayout
from PyQt5.QtCore import Qt
from app.ui.common import CyberLabel

class PostureCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #ffffff; 
                border-radius: 8px; 
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)
        
        self.posture_status = CyberLabel("✅ 姿态标准", 11, "#28a745", True)
        self.val_dist = CyberLabel("距离: 正常", 10, "#333333")
        self.val_shoulder = CyberLabel("肩斜: 0.0°", 10, "#666666")
        self.val_neck = CyberLabel("颈前: 0.0°", 10, "#666666")
        
        layout.addWidget(self.posture_status, 0, 0, 1, 2)
        layout.addWidget(self.val_dist, 1, 0, 1, 2)
        layout.addWidget(self.val_shoulder, 2, 0)
        layout.addWidget(self.val_neck, 2, 1)

    def update_data(self, a_data):
        """更新坐姿数据"""
        is_bad = a_data.get("is_hunchback") or a_data.get("is_shoulder_tilted")
        self.posture_status.setText("⚠️ 姿态异常" if is_bad else "✅ 姿态标准")
        self.posture_status.setStyleSheet(f"color: {'#dc3545' if is_bad else '#28a745'}; font-weight: bold; font-size: 11pt;")
        
        self.val_shoulder.setText(f"肩斜: {a_data.get('shoulder_tilt_angle', 0.0):.1f}°")
        self.val_neck.setText(f"颈前: {a_data.get('neck_tilt', 0.0):.1f}°")
        
        raw_dist = a_data.get('dist_screen', 'normal')
        dist_map = {"normal": "正常", "too_close": "太近", "too_far": "太远"}
        dist_text = f"{raw_dist:.1f} cm" if isinstance(raw_dist, (int, float)) else dist_map.get(str(raw_dist), "正常")
        self.val_dist.setText(f"距离: {dist_text}")