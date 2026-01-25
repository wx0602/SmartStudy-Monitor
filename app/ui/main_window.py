import time
import winsound
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QImage, QPixmap

from app.ai_worker import AIWorker
from app.ui.bubble import NotificationBubble
from app.ui.clock import ClockPanel
from app.ui.dashboard import DashboardPanel
# 务必确保这行导入存在
from app.ui.controls import ControlsPanel 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartStudy Monitor - Pro Control")
        self.setGeometry(100, 100, 1100, 680)
        # 注意：这里我们不再依赖 qt_material 的背景色，而是自己定义一个
        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")
        
        self.alarm_triggered = False
        
        self.current_issue = None; self.issue_start_time = 0
        self.alert_showing = False; self.alert_start_time = 0; self.last_alert_msg = ""
        self.last_severe_alert_time = 0
        
        self.threshold_map = {
            "phone": 1.5, "hunch": 2.0, "sleep": 2.5, 
            "posture": 3.0, "turtle": 3.0, "hands": 3.0, "gaze": 3.0
        }

        self.init_ui()
        
        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(self.check_alarm_status)
        self.system_timer.start(1000)

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # 1. 左侧视窗
        vp_container = QWidget()
        vp_layout = QVBoxLayout(vp_container); vp_layout.setContentsMargins(20, 20, 20, 20)
        self.video_frame = QFrame(); self.video_frame.setStyleSheet("background: black; border-radius: 12px;")
        v_layout = QVBoxLayout(self.video_frame); v_layout.setContentsMargins(0,0,0,0)
        
        self.video_label = QLabel("正在启动 AI..."); self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True); self.video_label.setStyleSheet("background: transparent;")
        v_layout.addWidget(self.video_label)
        vp_layout.addWidget(self.video_frame)
        root.addWidget(vp_container, stretch=1)

        self.mild_bubble = NotificationBubble(self.video_frame)
        self.severe_alert = QLabel(self.video_frame)
        self.severe_alert.setAlignment(Qt.AlignCenter); self.severe_alert.hide()
        self.severe_alert.setStyleSheet("QLabel { background-color: rgba(220, 53, 69, 220); color: white; border-radius: 15px; padding: 20px; font-family: 'Microsoft YaHei'; font-size: 28px; font-weight: bold; }")

        # 2. 右侧侧边栏
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(360)
        self.sidebar_container.setStyleSheet("background: #252525; border-left: 1px solid #333; color: #e0e0e0;")
        
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        self.dashboard = DashboardPanel()
        self.stack.addWidget(self.dashboard)
        
        self.clock_panel = ClockPanel()
        self.stack.addWidget(self.clock_panel)
        
        # 把 ControlsPanel 加回来
        self.controls_panel = ControlsPanel()
        self.stack.addWidget(self.controls_panel)
        
        sidebar_layout.addWidget(self.stack)
        root.addWidget(self.sidebar_container)
        self.sidebar_container.hide()

        # 3. 工具栏
        toolbar = QFrame(); toolbar.setFixedWidth(70)
        toolbar.setStyleSheet("background: #2b2b2b; border-left: 1px solid #444;")
        tb_layout = QVBoxLayout(toolbar)
        tb_layout.setContentsMargins(5, 20, 5, 20); tb_layout.setSpacing(20)
        
        self.btn_stats = self.create_btn("📊", lambda: self.switch_sidebar(0))
        tb_layout.addWidget(self.btn_stats)
        
        self.btn_clock = self.create_btn("⏰", lambda: self.switch_sidebar(1))
        tb_layout.addWidget(self.btn_clock)
        
        self.btn_ctrl = self.create_btn("⚙️", lambda: self.switch_sidebar(2))
        tb_layout.addWidget(self.btn_ctrl)
        
        tb_layout.addStretch()
        root.addWidget(toolbar)

    def create_btn(self, icon, func):
        btn = QPushButton(icon)
        btn.setFixedSize(50, 50); btn.setCursor(Qt.PointingHandCursor); btn.clicked.connect(func)
        # 这里移除了一些复杂的 CSS，交由全局 QSS 控制
        return btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        vw, vh = self.video_frame.width(), self.video_frame.height()
        self.severe_alert.setGeometry((vw - 320)//2, (vh - 90)//2, 320, 90)
        self.mild_bubble.move(vw - self.mild_bubble.width() - 20, vh - self.mild_bubble.height() - 20)

    def switch_sidebar(self, index):
        if self.sidebar_container.isVisible() and self.stack.currentIndex() == index:
            self.sidebar_container.hide()
            self.update_btn_styles(-1)
        else:
            self.sidebar_container.show()
            self.stack.setCurrentIndex(index)
            self.update_btn_styles(index)

    def update_btn_styles(self, active_index):
        base = "QPushButton { background: transparent; font-size: 24px; border: 1px solid #555; border-radius: 12px; color: #aaa; } QPushButton:hover { background: #333; border: 1px solid #00e5ff; color: #00e5ff; }"
        active_blue = "QPushButton { background: #2196f3; font-size: 24px; border: none; border-radius: 12px; color: white; }"
        active_orange = "QPushButton { background: #ff9800; font-size: 24px; border: none; border-radius: 12px; color: white; }"
        active_grey = "QPushButton { background: #607d8b; font-size: 24px; border: none; border-radius: 12px; color: white; }"
        
        self.btn_stats.setStyleSheet(base)
        self.btn_clock.setStyleSheet(base)
        self.btn_ctrl.setStyleSheet(base)
        
        if active_index == 0: self.btn_stats.setStyleSheet(active_blue)
        elif active_index == 1: self.btn_clock.setStyleSheet(active_orange)
        elif active_index == 2: self.btn_ctrl.setStyleSheet(active_grey)

    def update_dashboard(self, data):
        if "Error" in data: return
        a = data.get("A", {}); b = data.get("B", {}); c = data.get("C", {}); h = c.get("手部行为", {})
        
        config = self.controls_panel.get_config()
        
        issue = None; itype = "none"
        if config["phone"] and c.get("手机使用", {}).get("使用手机"): issue = "放下手机，专心学习"; itype = "phone"
        elif config["hunch"] and a.get("is_hunchback"): issue = "严重驼背！请挺直"; itype = "hunch"
        elif config["sleep"] and b.get("blink_state") == "close": issue = "醒醒，别睡着了"; itype = "sleep"
        elif config["hands"]:
            if h.get("托腮"): issue = "不要总是托腮哦"; itype = "hands"
            elif h.get("频繁摸脸"): issue = "别总摸脸，容易分心"; itype = "hands"
            elif h.get("扶额") or h.get("频繁撑头"): issue = "头痛吗？注意休息"; itype = "hands"
        
        if not issue:
            if config["posture"]:
                if a.get("is_shoulder_tilted"): issue = "身体侧倾"; itype = "posture"
                elif a.get("is_neck_tilted"): issue = "头部姿态不正"; itype = "posture"
            if not issue and config["turtle"] and a.get("is_head_forward"): issue = "脖子前伸 (乌龟颈)"; itype = "turtle"
            if not issue and config["gaze"] and b.get("gaze_off"): issue = "视线偏离屏幕"; itype = "gaze"

        now = time.time()
        if issue != self.current_issue: self.current_issue = issue; self.issue_start_time = now
        duration = now - self.issue_start_time
        trigger = (issue and duration >= self.threshold_map.get(itype, 999))

        locked = self.alert_showing and (now - self.alert_start_time < 3.0)
        if locked:
            if trigger and issue != self.last_alert_msg: self.do_alert(issue, itype, config["volume"])
        else:
            if trigger: self.do_alert(issue, itype, config["volume"])
            else: self.alert_showing = False; self.severe_alert.hide(); self.mild_bubble.hide(); self.last_alert_msg = ""

        if self.sidebar_container.isVisible() and self.stack.currentIndex() == 0:
            self.dashboard.update_data(a, b, c)

    def do_alert(self, msg, itype, volume):
        self.alert_showing = True
        if msg != self.last_alert_msg: self.alert_start_time = time.time(); self.last_alert_msg = msg
        if itype in ["phone", "hunch"]: self.show_severe_alert(msg, volume); self.mild_bubble.hide()
        else: self.severe_alert.hide(); self.mild_bubble.show_message(msg)

    def show_severe_alert(self, msg, volume, force=False):
        self.severe_alert.setText(f"🚫 {msg}"); self.severe_alert.show(); self.severe_alert.raise_()
        now = time.time()
        if not force and now - self.last_severe_alert_time > 3.0:
            if volume > 0:
                try: winsound.Beep(1000, 300)
                except: pass
            self.last_severe_alert_time = now

    def check_alarm_status(self):
        s = self.clock_panel.get_settings()
        if not s["is_on"]: self.alarm_triggered = False; return
        now = QTime.currentTime()
        tgt = s["target_time"]
        if now.hour() == tgt.hour() and now.minute() == tgt.minute() and now.second() == 0:
            if not self.alarm_triggered:
                self.trigger_alarm(s["volume"]); self.alarm_triggered = True
        elif now.second() > 5: self.alarm_triggered = False

    def trigger_alarm(self, volume):
        self.show_severe_alert("⏰ 闹钟时间到！", volume, force=True)
        if volume > 0:
            try:
                for _ in range(3): winsound.Beep(1500, 400); time.sleep(0.1)
            except: pass
        QTimer.singleShot(3000, self.severe_alert.hide)

    def start_worker(self):
        self.thread = AIWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_dashboard)
        self.thread.start()

    def update_image(self, cv_img):
        h, w, ch = cv_img.shape
        qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))