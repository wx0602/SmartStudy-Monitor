from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QGridLayout, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont

# 引入我们刚才拆分出去的组件
from app.ui_components import CyberLabel, GazeRadar, StatusLight
from app.ai_worker import AIWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartStudy Monitor - Modular")
        self.setGeometry(100, 100, 1400, 850)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")
        self.init_ui()
        self.thread = None

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 左侧: 视频区
        video_container = QFrame()
        video_container.setStyleSheet("background: black; border: 2px solid #333; border-radius: 8px;")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_label = QLabel("初始化...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True) 
        video_layout.addWidget(self.video_label)
        main_layout.addWidget(video_container, stretch=65)

        # 右侧: 面板区
        panel_scroll = QWidget() 
        panel_layout = QVBoxLayout(panel_scroll)
        
        title = QLabel("🛡️ SMART MONITOR")
        title.setFont(QFont("Impact", 24))
        title.setStyleSheet("color: #00e5ff; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(title)

        self.create_attention_panel(panel_layout)
        self.create_posture_panel(panel_layout)
        self.create_behavior_panel(panel_layout)
        panel_layout.addStretch()
        
        right_container = QFrame()
        right_container.setStyleSheet("background: #1e1e1e; border-radius: 12px;")
        right_container.setLayout(panel_layout)
        main_layout.addWidget(right_container, stretch=35)

    def start_worker(self):
        self.thread = AIWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_dashboard)
        self.thread.start()

    def create_card_frame(self, layout, title):
        frame = QFrame()
        frame.setStyleSheet("background: #252525; border-radius: 8px; padding: 5px;")
        vbox = QVBoxLayout(frame)
        lbl = QLabel(title)
        lbl.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        lbl.setStyleSheet("color: #aaaaaa; border-bottom: 1px solid #444; padding-bottom: 5px;")
        vbox.addWidget(lbl)
        layout.addWidget(frame)
        return vbox

    def create_attention_panel(self, parent_layout):
        layout = self.create_card_frame(parent_layout, "🧠 注意力 & 视线")
        
        self.attn_status_label = QLabel("🟢 实时监测中 (免校准)")
        self.attn_status_label.setStyleSheet("color: #69f0ae; font-size: 10pt;")
        layout.addWidget(self.attn_status_label)

        row1 = QHBoxLayout()
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #00e676; }")
        row1.addWidget(self.score_bar)
        self.perclos_val = CyberLabel("疲劳: --", 10, "#ffcc80")
        row1.addWidget(self.perclos_val)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        radar_container = QVBoxLayout()
        self.gaze_radar = GazeRadar(size=90)
        radar_container.addWidget(self.gaze_radar)
        radar_container.setAlignment(Qt.AlignCenter)
        row2.addLayout(radar_container)
        
        head_grid = QGridLayout()
        self.val_yaw = CyberLabel("Yaw: --", 10, "#81d4fa")   
        self.val_pitch = CyberLabel("Pitch: --", 10, "#81d4fa") 
        self.val_blink = CyberLabel("Eye: --", 10, "#b39ddb")
        self.val_gaze_off = StatusLight("视线偏离", "#ff5252")
        head_grid.addWidget(self.val_yaw, 0, 0)
        head_grid.addWidget(self.val_pitch, 1, 0)
        head_grid.addWidget(self.val_blink, 0, 1)
        head_grid.addWidget(self.val_gaze_off, 1, 1)
        row2.addLayout(head_grid)
        layout.addLayout(row2)

    def create_posture_panel(self, parent_layout):
        layout = self.create_card_frame(parent_layout, "🦴 坐姿分析")
        self.posture_status = CyberLabel("状态: 初始化...", 14, "#ffffff", True)
        self.posture_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.posture_status)
        
        grid = QGridLayout()
        self.val_shoulder = CyberLabel("肩倾: 0°", 11)
        self.val_neck = CyberLabel("颈倾: 0°", 11)
        self.val_lean = CyberLabel("躯干: --", 11)
        grid.addWidget(self.val_shoulder, 0, 0)
        grid.addWidget(self.val_neck, 0, 1)
        grid.addWidget(self.val_lean, 1, 0)
        layout.addLayout(grid)
        
        stab_layout = QHBoxLayout()
        stab_layout.addWidget(QLabel("稳定性:"))
        self.stability_bar = QProgressBar()
        self.stability_bar.setRange(0, 100)
        self.stability_bar.setStyleSheet("QProgressBar::chunk { background-color: #29b6f6; }")
        stab_layout.addWidget(self.stability_bar)
        layout.addLayout(stab_layout)

    def create_behavior_panel(self, parent_layout):
        layout = self.create_card_frame(parent_layout, "🎬 行为识别")
        grid = QGridLayout()
        self.light_phone = StatusLight("📱 玩手机")
        self.light_chin = StatusLight("🤔 托腮", "#ff9100")
        self.light_face = StatusLight("👋 摸脸", "#ff9100")
        self.light_head = StatusLight("🤯 扶额", "#ff9100")
        self.light_away = StatusLight("🚪 离席", "#9e9e9e")
        grid.addWidget(self.light_phone, 0, 0, 1, 2) 
        grid.addWidget(self.light_chin, 1, 0)
        grid.addWidget(self.light_face, 1, 1)
        grid.addWidget(self.light_head, 2, 0)
        grid.addWidget(self.light_away, 2, 1)
        layout.addLayout(grid)

    def update_image(self, qt_img):
        # 这里的参数已经是 QImage 了 (从 Worker 发 RGB numpy array -> Worker 内部不做转换 -> 还是在 UI 线程转换比较安全? 
        # 不，Worker 线程发出 ndarray，UI 线程转 QImage 更稳定，防止跨线程传递大对象崩溃
        # 我们稍微调整一下 logic，Worker 发出 ndarray, 这里转 QImage
        pass # 下面的 update_image 逻辑覆盖了这里

    def update_image(self, cv_img):
        # 将 RGB 数组转为 QImage
        h, w, ch = cv_img.shape
        qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def update_dashboard(self, data):
        if "Error" in data:
            self.posture_status.setText("❌ 摄像头故障")
            return
        
        # A
        a = data.get("A", {})
        is_hunch = a.get("is_hunchback", False)
        status = "⚠️ 驼背" if is_hunch else ("⚠️ 侧倾" if a.get("is_shoulder_tilted") else "✅ 正常")
        color = "#ff5252" if is_hunch else "#69f0ae"
        self.posture_status.setText(status)
        self.posture_status.setStyleSheet(f"color: {color}; font-size: 14pt; font-weight: bold;")
        self.val_shoulder.setText(f"肩倾: {a.get('shoulder_tilt_angle', 0)}°")
        self.val_neck.setText(f"颈倾: {a.get('neck_tilt', 0)}°")
        self.val_lean.setText(f"躯干: {a.get('body_lean', '-')}")
        self.stability_bar.setValue(int(a.get("stability_score", 100)))

        # B
        b = data.get("B", {})
        self.score_bar.setValue(int(b.get("attention_score", 0)))
        self.perclos_val.setText(f"疲劳: {b.get('perclos', 0)}")
        
        yaw = b.get("yaw_angle")
        pitch = b.get("pitch_angle")
        blink = b.get("blink_state")
        self.val_yaw.setText(f"Yaw: {yaw}°" if yaw is not None else "Yaw: --")
        self.val_pitch.setText(f"Pitch: {pitch}°" if pitch is not None else "Pitch: --")
        self.val_blink.setText(f"Eye: {blink}" if blink else "Eye: --")
        self.val_gaze_off.set_status(b.get("gaze_off", False))
        gx = b.get("gaze_x")
        gy = b.get("gaze_y")
        self.gaze_radar.update_gaze(gx if gx else 0, gy if gy else 0, True)

        # C
        c = data.get("C", {})
        self.light_phone.set_status(c.get("手机使用", {}).get("使用手机", False))
        hands = c.get("手部行为", {})
        self.light_chin.set_status(hands.get("托腮", False))
        self.light_face.set_status(hands.get("频繁摸脸", False))
        self.light_head.set_status(hands.get("扶额", False) or hands.get("频繁撑头", False))
        self.light_away.set_status(c.get("离席检测", {}).get("离席", False))