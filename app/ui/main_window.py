import time
import winsound
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QStackedWidget, QPushButton)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

from app.ai_worker import AIWorker
from app.ui.dashboard import HorizontalMonitorBar
from app.ui.clock import ClockPanel
from app.ui.controls import ControlsPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartStudy Monitor (Light Pro)")
        self.setMinimumSize(1280, 850)
        
        self.current_alert_level = None
        self.pending_issue = None
        self.issue_start_time = 0
        self.alert_display_start = 0
        self.last_beep_time = 0
        
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # === 1. 左侧 ===
        left_side = QWidget()
        left_layout = QVBoxLayout(left_side)
        left_layout.setContentsMargins(15, 15, 10, 15)

        # 视频框
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background: black; border-radius: 8px; border: 1px solid #cccccc;")
        vf_layout = QVBoxLayout(self.video_frame)
        vf_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel("正在启动视觉系统...")
        self.video_label.setStyleSheet("color: white;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True)
        vf_layout.addWidget(self.video_label)
        left_layout.addWidget(self.video_frame, stretch=7)

        # 悬浮弹窗 (Type 2 - 中间红框)
        self.alert_type2 = QLabel(self.video_frame)
        self.alert_type2.setAlignment(Qt.AlignCenter)
        self.alert_type2.setStyleSheet("""
            background-color: #dc3545; 
            color: white; 
            font-size: 32px; 
            font-weight: bold; 
            border-radius: 8px; 
            padding: 20px;
        """)
        self.alert_type2.hide()

        # 悬浮弹窗 (Type 1 - 右下黄框)
        self.alert_type1 = QLabel(self.video_frame)
        self.alert_type1.setAlignment(Qt.AlignCenter)
        self.alert_type1.setStyleSheet("""
            background-color: #ffc107; 
            color: #333; 
            font-size: 20px; 
            font-weight: bold; 
            border-radius: 8px; 
            padding: 10px 20px;
        """)
        self.alert_type1.hide()

        # 下方数据栏
        self.bottom_monitor = HorizontalMonitorBar()
        self.bottom_monitor.setFixedHeight(180)
        left_layout.addWidget(self.bottom_monitor, stretch=3)

        root.addWidget(left_side, 1)

        # === 2. 右侧 ===
        self.right_sidebar = QFrame()
        self.right_sidebar.setFixedWidth(320)
        self.right_sidebar.setStyleSheet("""
            QFrame { background: #f8f9fa; border-left: 1px solid #e0e0e0; }
            QScrollBar:horizontal { height: 0px; }
        """)
        
        side_layout = QVBoxLayout(self.right_sidebar)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)
        
        self.side_status = QLabel("系统就绪")
        self.side_status.setAlignment(Qt.AlignCenter)
        self.side_status.setStyleSheet("color: #333; font-size: 14px; font-weight: bold; padding: 10px;")
        side_layout.addWidget(self.side_status)

        self.stack = QStackedWidget()
        self.clock_panel = ClockPanel()
        self.controls_panel = ControlsPanel()
        self.clock_panel.setMinimumWidth(0)
        self.controls_panel.setMinimumWidth(0)
        
        self.stack.addWidget(self.clock_panel)
        self.stack.addWidget(self.controls_panel)
        side_layout.addWidget(self.stack)

        root.addWidget(self.right_sidebar, 0)

        # === 3. 工具栏 ===
        toolbar = QFrame()
        toolbar.setFixedWidth(60)
        toolbar.setStyleSheet("background: #ffffff; border-left: 1px solid #e0e0e0;")
        t_lay = QVBoxLayout(toolbar)
        self.btn_clock = self._create_btn("⏰", 0)
        self.btn_ctrl = self._create_btn("⚙️", 1)
        t_lay.addWidget(self.btn_clock); t_lay.addWidget(self.btn_ctrl); t_lay.addStretch()
        root.addWidget(toolbar, 0)

    def _create_btn(self, icon, idx):
        btn = QPushButton(icon)
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background: transparent; font-size: 22px; border: 1px solid #e0e0e0; border-radius: 10px; color: #333; } 
            QPushButton:hover { background: #f0f0f0; color: #007bff; border-color: #007bff; }
        """)
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(idx))
        return btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'video_frame'):
            vw, vh = self.video_frame.width(), self.video_frame.height()
            w2, h2 = 400, 100
            self.alert_type2.setGeometry((vw - w2)//2, (vh - h2)//2, w2, h2)
            w1, h1 = 260, 60
            self.alert_type1.setGeometry(vw - w1 - 20, vh - h1 - 20, w1, h1)

    def update_dashboard(self, data):
        if "Error" in data: return
        a, b, c = data.get("A", {}), data.get("B", {}), data.get("C", {})
        config = self.controls_panel.get_config()
        now = time.time()

        self.bottom_monitor.update_data(a, b, c)

        issue_msg = None
        issue_level = 0 

        # === 第一梯队：重度 (Type 2 - 红框) ===
        if config["phone"] and c.get("手机使用", {}).get("使用手机"):
            issue_msg, issue_level = "🚫 禁止使用手机", 2
        elif config["away"] and c.get("离席检测", {}).get("离席"):
            issue_msg, issue_level = "🚫 检测到离席", 2
            
        # === 第二梯队：轻度 (Type 1 - 黄气泡) ===
        if not issue_msg:
            # 1. 距离过近 (新增)
            if config["dist"] and str(a.get("dist_screen")) == "too_close":
                issue_msg, issue_level = "👀 离屏幕太近了", 1
            
            # 2. 闭眼 (睡眠)
            elif config["sleep"] and b.get("blink_state") == "close":
                issue_msg, issue_level = "👁️ 请勿闭眼", 1
            
            # 3. 手部行为
            elif config["chin"] and c.get("手部行为", {}).get("托腮"):
                issue_msg, issue_level = "🤔 请勿托腮", 1
            elif config["face"] and c.get("手部行为", {}).get("频繁摸脸"):
                issue_msg, issue_level = "👋 不要摸脸", 1
            
            # 4. 姿态问题
            elif config["posture"]:
                if a.get("neck_tilt", 0) > 25: 
                    issue_msg, issue_level = "🦒 脖子前伸", 1
                elif a.get("is_hunchback") or abs(a.get("shoulder_tilt_angle", 0)) > 5:
                    issue_msg, issue_level = "🦴 坐姿不正", 1

        # 状态机处理
        if issue_msg:
            if issue_msg != self.pending_issue:
                self.pending_issue = issue_msg
                self.issue_start_time = now
            
            if now - self.issue_start_time >= 2.0:
                self.show_alert(issue_msg, issue_level)
                if now - self.last_beep_time > 4.0 and config["volume"] > 0:
                    freq = 1000 if issue_level == 2 else 600
                    winsound.Beep(freq, 200)
                    self.last_beep_time = now
        else:
            self.pending_issue = None
            if self.current_alert_level and (now - self.alert_display_start >= 3.0):
                self.hide_alerts()

    def show_alert(self, msg, level):
        now = time.time()
        if self.current_alert_level and (now - self.alert_display_start < 3.0):
            if level <= self.current_alert_level: return

        self.current_alert_level = level
        self.alert_display_start = now
        
        if level == 2:
            self.alert_type1.hide()
            self.alert_type2.setText(msg)
            self.alert_type2.show()
            self.alert_type2.raise_()
        else:
            self.alert_type2.hide()
            self.alert_type1.setText(msg)
            self.alert_type1.show()
            self.alert_type1.raise_()

    def hide_alerts(self):
        self.current_alert_level = None
        self.alert_type1.hide()
        self.alert_type2.hide()

    def start_worker(self):
        self.thread = AIWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_dashboard)
        self.thread.start()

    def update_image(self, cv_img):
        h, w, ch = cv_img.shape
        qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))