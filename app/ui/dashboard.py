from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget, QHBoxLayout, QGridLayout, QProgressBar
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from app.ui.common import CyberLabel, StatusLight, GazeRadar

class DashboardPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self.setStyleSheet("background: #1e1e1e; border-left: 1px solid #333; color: #e0e0e0;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 0)
        
        title = QLabel("监测数据终端")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #888; background: transparent; margin-bottom: 10px;")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea {background: transparent;} QScrollBar:vertical {width:6px; background:transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        
        # 关键修改：改名为 content_layout
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(15, 0, 15, 20)
        self.content_layout.setSpacing(15)
        
        self.create_attention_panel()
        self.create_posture_panel()
        self.create_behavior_panel()
        self.content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_card(self, title):
        frame = QFrame()
        frame.setStyleSheet("background: #252525; border-radius: 8px; padding: 12px; border: 1px solid #333;")
        vbox = QVBoxLayout(frame)
        lbl = QLabel(title)
        lbl.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        lbl.setStyleSheet("color: #aaa; padding-bottom: 8px; border-bottom: 1px solid #444;")
        vbox.addWidget(lbl)
        
        # 使用新名字
        self.content_layout.addWidget(frame)
        return vbox

    # ... 以下代码(create_attention_panel等)内容不变，省略以节省篇幅 ...
    # ... 请保留之前的 create_attention_panel, create_posture_panel, create_behavior_panel, update_data ...
    # 注意：这些函数里不需要改动，因为它们调用的是 self.create_card，而 create_card 我们已经改好了。

    # (为了确保你复制粘贴不出错，这里把 create_card 后面需要保留的函数框架写出来)
    def create_attention_panel(self):
        layout = self.create_card("🧠 注意力 & 视线")
        # ... 原代码 ...
        # (这里需要把之前的 create_attention_panel 内容填进去)
        row_s = QHBoxLayout(); self.attn_status = QLabel("监测中"); self.attn_status.setStyleSheet("color: #69f0ae;")
        self.val_perclos = CyberLabel("疲劳: 0.0", 10, "#ffcc80"); row_s.addWidget(self.attn_status); row_s.addWidget(self.val_perclos); layout.addLayout(row_s)
        self.score_bar = QProgressBar(); self.score_bar.setRange(0, 100); self.score_bar.setStyleSheet("QProgressBar {height: 8px; border:none; background:#333;} QProgressBar::chunk { background-color: #00e676; }"); layout.addWidget(self.score_bar)
        row_r = QHBoxLayout(); radar_box = QVBoxLayout(); self.gaze_radar = GazeRadar(size=80); radar_box.addWidget(self.gaze_radar); radar_box.setAlignment(Qt.AlignCenter); row_r.addLayout(radar_box)
        grid = QGridLayout(); self.val_yaw = CyberLabel("Yaw: 0°", 9, "#81d4fa"); self.val_pitch = CyberLabel("Pitch: 0°", 9, "#81d4fa"); self.val_blink = CyberLabel("Eye: --", 9, "#b39ddb"); self.val_gaze_off = StatusLight("视线偏离", "#ff5252"); grid.addWidget(self.val_yaw, 0, 0); grid.addWidget(self.val_pitch, 1, 0); grid.addWidget(self.val_blink, 2, 0); grid.addWidget(self.val_gaze_off, 3, 0); row_r.addLayout(grid); layout.addLayout(row_r)
        row_num = QHBoxLayout(); self.val_away = CyberLabel("分心: 0%", 9, "#888"); self.val_down = CyberLabel("低头: 0%", 9, "#888"); row_num.addWidget(self.val_away); row_num.addWidget(self.val_down); layout.addLayout(row_num)

    def create_posture_panel(self):
        layout = self.create_card("🦴 坐姿分析")
        self.posture_status = CyberLabel("状态: 初始化", 12, "#fff", True)
        layout.addWidget(self.posture_status)
        grid = QGridLayout()
        self.val_shoulder = CyberLabel("肩倾: 0°", 10); self.val_neck = CyberLabel("颈倾: 0°", 10); self.val_head_fwd = CyberLabel("前伸: 0.0", 10); self.val_dist = CyberLabel("距离: --", 10)
        grid.addWidget(self.val_shoulder, 0, 0); grid.addWidget(self.val_neck, 0, 1); grid.addWidget(self.val_head_fwd, 1, 0); grid.addWidget(self.val_dist, 1, 1); layout.addLayout(grid)
        row = QHBoxLayout(); row.addWidget(QLabel("稳定性:")); self.stability_bar = QProgressBar(); self.stability_bar.setRange(0, 100); self.stability_bar.setStyleSheet("QProgressBar {height: 6px; border:none; background:#333;} QProgressBar::chunk { background-color: #29b6f6; }"); row.addWidget(self.stability_bar); layout.addLayout(row)

    def create_behavior_panel(self):
        layout = self.create_card("🎬 行为识别")
        grid = QGridLayout()
        self.lights = { "phone": StatusLight("📱 玩手机"), "chin": StatusLight("🤔 托腮", "#ff9100"), "face": StatusLight("👋 摸脸", "#ff9100"), "head": StatusLight("🤯 扶额", "#ff9100"), "away": StatusLight("🚪 离席", "#9e9e9e") }
        grid.addWidget(self.lights["phone"], 0, 0, 1, 2); grid.addWidget(self.lights["chin"], 1, 0); grid.addWidget(self.lights["face"], 1, 1); grid.addWidget(self.lights["head"], 2, 0); grid.addWidget(self.lights["away"], 2, 1); layout.addLayout(grid)

    def update_data(self, a, b, c):
        self.score_bar.setValue(int(b.get("attention_score", 0))); self.val_perclos.setText(f"疲劳: {b.get('perclos', 0)}"); self.val_away.setText(f"分心: {b.get('away_ratio', 0)*100:.0f}%"); self.val_down.setText(f"低头: {b.get('down_ratio', 0)*100:.0f}%"); self.val_yaw.setText(f"Yaw: {b.get('yaw_angle', 0)}°"); self.val_pitch.setText(f"Pitch: {b.get('pitch_angle', 0)}°"); self.val_blink.setText(f"Eye: {b.get('blink_state', '-')}"); self.val_gaze_off.set_status(b.get("gaze_off", False)); gx = b.get("gaze_x"); gy = b.get("gaze_y"); self.gaze_radar.update_gaze(gx if gx else 0, gy if gy else 0, True)
        if a.get("is_hunchback"): status, col = "⚠️ 严重驼背", "#ff5252"
        elif a.get("is_shoulder_tilted"): status, col = "⚠️ 身体侧倾", "#ffab40"
        elif a.get("is_head_forward"): status, col = "⚠️ 脖子前伸", "#ffab40"
        else: status, col = "✅ 坐姿端正", "#69f0ae"
        self.posture_status.setText(status); self.posture_status.setStyleSheet(f"color: {col}; font-weight: bold; font-size: 12pt;"); self.val_shoulder.setText(f"肩倾: {a.get('shoulder_tilt_angle', 0)}°"); self.val_neck.setText(f"颈倾: {a.get('neck_tilt', 0)}°"); self.val_head_fwd.setText(f"前伸: {a.get('head_forward_degree', 0):.2f}"); d = a.get("dist_screen", "--"); self.val_dist.setText(f"距离: {d:.1f}cm" if isinstance(d, (int, float)) else f"距离: {d}"); self.stability_bar.setValue(int(a.get("stability_score", 100)))
        self.lights["phone"].set_status(c.get("手机使用", {}).get("使用手机", False)); h = c.get("手部行为", {}); self.lights["chin"].set_status(h.get("托腮", False)); self.lights["face"].set_status(h.get("频繁摸脸", False)); self.lights["head"].set_status(h.get("扶额", False) or h.get("频繁撑头", False)); self.lights["away"].set_status(c.get("离席检测", {}).get("离席", False))