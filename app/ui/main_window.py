import time
import winsound

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QPushButton,
    QStackedLayout
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QImage, QPixmap

from app.ui.rounded_image_label import RoundedImageLabel
from app.ai_worker import AIWorker
from app.ui.dashboard import HorizontalMonitorBar
from app.ui.clock import ClockPanel
from app.ui.controls import ControlsPanel

from app.ui.bubble import ToastBubble, ModalBubble

from app.ui.background import BackgroundWidget
from app.ui.theme import theme_by_name, qss
from app.ui.sidebar_bg import SidebarBackgroundFrame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartStudy Monitor")
        self.setMinimumSize(1280, 850)

        self._theme_name = "light"
        self._theme = theme_by_name(self._theme_name)

        self.pending_issue = None
        self.issue_start_time = 0
        self.last_beep_time = 0

        # Type1 冷却（可重复触发）
        self._toast_last_time_by_msg = {}
        self._toast_cooldown = 3.0

        # Type2：必须手动关闭
        self._type2_open = False
        self._type2_last_close_time = 0.0       # ✅ 用 close_time 控制再次弹出
        self._type2_reopen_delay = 2.0          # ✅ 叉掉后至少等 2 秒再允许弹出（防刷屏）

        self.init_ui()
        self.apply_theme(self._theme_name)

    # =========================
    # Theme
    # =========================
    def apply_theme(self, name: str):
        self._theme_name = name
        self._theme = theme_by_name(name)

        self.central_bg.set_background(self._theme.bg, self._theme.bg_image)
        self.right_sidebar.set_bg_image(self._theme.sidebar_bg_image)
        self.setStyleSheet(qss(self._theme))

        # 同步 bubble 主题
        self.toast.set_theme(self._theme_name)
        self.modal.set_theme(self._theme_name)

    def toggle_theme(self):
        self.apply_theme("dark" if self._theme_name == "light" else "light")

    # =========================
    # UI
    # =========================
    def init_ui(self):
        self.central_bg = BackgroundWidget()
        self.setCentralWidget(self.central_bg)

        root = QHBoxLayout(self.central_bg)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # === 左侧 ===
        left_side = QWidget()
        left_layout = QVBoxLayout(left_side)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        self.video_frame = QFrame()
        self.video_frame.setObjectName("HeroCard")

        # StackAll：底层视频 + 顶层 overlay（Type1）
        self.video_stack = QStackedLayout(self.video_frame)
        self.video_stack.setContentsMargins(10, 10, 10, 10)
        self.video_stack.setStackingMode(QStackedLayout.StackAll)

        self.video_label = RoundedImageLabel(radius=25)
        self.video_label.setObjectName("VideoInner")
        self.video_label.setText("正在启动视觉系统...")
        self.video_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.overlay = QWidget()
        self.overlay.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay.setStyleSheet("background: transparent;")
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.video_stack.addWidget(self.video_label)
        self.video_stack.addWidget(self.overlay)

        # ✅ 关键：不要给视频卡加 QGraphicsDropShadowEffect（高频刷新极易触发 QPainter 报错）
        # 如果你想要“阴影感”，建议走 QSS 高光边/渐变，而不是 graphicsEffect

        left_layout.addWidget(self.video_frame, stretch=7)

        # ✅ Type1（轻度）挂 overlay（不影响点击）
        self.toast = ToastBubble(self.overlay)

        # ✅ Type2（重度）顶层弹窗（独立窗口，永远可点）
        self.modal = ModalBubble()
        self.modal.closed.connect(self.on_modal_closed)

        self.bottom_monitor = HorizontalMonitorBar()
        self.bottom_monitor.setFixedHeight(180)
        left_layout.addWidget(self.bottom_monitor, stretch=3)

        root.addWidget(left_side, 1)

        # === 右侧 ===
        self.right_sidebar = SidebarBackgroundFrame(radius=14)
        self.right_sidebar.setObjectName("RightSidebar")
        self.right_sidebar.setFixedWidth(320)

        side_layout = QVBoxLayout(self.right_sidebar)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)

        self.sidebar_content = QFrame()
        self.sidebar_content.setObjectName("SidebarContent")
        side_layout.addWidget(self.sidebar_content, 0)
        side_layout.addStretch(1)

        content_layout = QVBoxLayout(self.sidebar_content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)

        self.side_status = QLabel("系统就绪")
        self.side_status.setObjectName("Title")
        self.side_status.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.side_status)

        self.stack = QStackedWidget()
        self.clock_panel = ClockPanel()
        self.controls_panel = ControlsPanel()
        self.stack.addWidget(self.clock_panel)
        self.stack.addWidget(self.controls_panel)
        content_layout.addWidget(self.stack, 1)

        root.addWidget(self.right_sidebar, 0)

        # === 工具栏 ===
        toolbar = QFrame()
        toolbar.setObjectName("Card")
        toolbar.setFixedWidth(68)

        t_lay = QVBoxLayout(toolbar)
        t_lay.setContentsMargins(10, 10, 10, 10)
        t_lay.setSpacing(10)

        self.btn_clock = self._create_btn("⏰", lambda: self.stack.setCurrentIndex(0))
        self.btn_ctrl = self._create_btn("⚙️", lambda: self.stack.setCurrentIndex(1))
        self.btn_theme = self._create_btn("🌓", self.toggle_theme)

        t_lay.addWidget(self.btn_clock)
        t_lay.addWidget(self.btn_ctrl)
        t_lay.addStretch(1)
        t_lay.addWidget(self.btn_theme)

        root.addWidget(toolbar, 0)

    def _create_btn(self, icon: str, cb):
        btn = QPushButton(icon)
        btn.setObjectName("ToolBtn")
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(cb)
        return btn

    # =========================
    # Geometry helpers
    # =========================
    def _video_frame_global_rect(self) -> QRect:
        top_left = self.video_frame.mapToGlobal(self.video_frame.rect().topLeft())
        return QRect(top_left, self.video_frame.size())

    # =========================
    # Modal callbacks
    # =========================
    def on_modal_closed(self):
        """
        ✅ 关键：允许 Type2 重复触发
        - 关闭时记录关闭时间（用于 reopen delay）
        - 重置 pending_issue / issue_start_time，让同一条违规也能重新蓄力触发
        """
        self._type2_open = False
        self._type2_last_close_time = time.time()

        # ✅ 不重置这俩的话：同一条 issue 会卡死，后续永远不再触发
        self.pending_issue = None
        self.issue_start_time = 0

    # =========================
    # Data / Alert logic
    # =========================
    def update_dashboard(self, data):
        if "Error" in data:
            return

        a, b, c = data.get("A", {}), data.get("B", {}), data.get("C", {})
        config = self.controls_panel.get_config()
        now = time.time()

        self.bottom_monitor.update_data(a, b, c)

        issue_msg = None
        issue_level = 0

        # Type2：重度
        if config["phone"] and c.get("手机使用", {}).get("使用手机"):
            issue_msg, issue_level = "禁止使用手机", 2
        elif config["away"] and c.get("离席检测", {}).get("离席"):
            issue_msg, issue_level = "检测到离席", 2

        # Type1：轻度
        if not issue_msg:
            if config["dist"] and str(a.get("dist_screen")) == "too_close":
                issue_msg, issue_level = "离屏幕太近了", 1
            elif config["sleep"] and b.get("blink_state") == "close":
                issue_msg, issue_level = "请勿闭眼", 1
            elif config["chin"] and c.get("手部行为", {}).get("托腮"):
                issue_msg, issue_level = "请勿托腮", 1
            elif config["face"] and c.get("手部行为", {}).get("频繁摸脸"):
                issue_msg, issue_level = "不要摸脸", 1
            elif config["posture"]:
                if a.get("neck_tilt", 0) > 25:
                    issue_msg, issue_level = "脖子前伸", 1
                elif a.get("is_hunchback") or abs(a.get("shoulder_tilt_angle", 0)) > 5:
                    issue_msg, issue_level = "坐姿不正", 1

        # 蓄力 2 秒（只有持续存在才触发）
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
            # 违规消失：解锁蓄力
            self.pending_issue = None
            self.issue_start_time = 0
            # Type2 不自动消失：不动 modal

    def show_alert(self, msg, level):
        now = time.time()

        # ===== Type2（重度）：必须手动关闭 =====
        if level == 2:
            # 已打开：仅更新内容+居中
            if self._type2_open and self.modal.isVisible():
                self.modal.show_at(msg, self._video_frame_global_rect())
                return

            # ✅ 叉掉后延迟 reopen（防刷屏）
            if (now - self._type2_last_close_time) < self._type2_reopen_delay:
                return

            self._type2_open = True
            self.modal.show_at(msg, self._video_frame_global_rect())
            return

        # ===== Type1（轻度）：Type2 显示时不弹 =====
        if self.modal.isVisible():
            return

        # Type1 冷却：同一 msg 3 秒内不重复弹
        last_t = self._toast_last_time_by_msg.get(msg, 0.0)
        if (now - last_t) < self._toast_cooldown:
            return

        self._toast_last_time_by_msg[msg] = now
        self.toast.show_toast(msg, duration_ms=1200)
        self.toast.raise_()

    # =========================
    # Worker
    # =========================
    def start_worker(self):
        self.thread = AIWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_dashboard)
        self.thread.start()

    def update_image(self, cv_img):
        h, w, ch = cv_img.shape
        qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

        # overlay 永远在视频上
        self.overlay.raise_()
        if self.toast.isVisible():
            self.toast.raise_()
