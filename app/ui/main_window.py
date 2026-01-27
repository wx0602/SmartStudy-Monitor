import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QPushButton,
    QStackedLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QImage, QPixmap

from app.audio_manager import SoundMgr
from app.ai_worker import AIWorker

# 导入路径指向分类文件夹
from app.ui.styles import (
    theme_by_name, qss, 
    BackgroundWidget, SidebarBackgroundFrame
)
from app.ui.widgets import (
    RoundedImageLabel, ToastBubble, ModalBubble, QuitDialog
)
from app.ui.panels import (
    HorizontalMonitorBar, ClockPanel, 
    ControlsPanel, ToDoPanel
)


class MainWindow(QMainWindow):
    """
    主应用程序窗口。

    负责整合 UI 组件、管理 AI 工作线程、处理违规检测逻辑以及响应用户交互。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartStudy Monitor")
        self.setMinimumSize(1280, 850)

        # 初始化主题配置
        self._theme_name = "light"
        self._theme = theme_by_name(self._theme_name)

        # 状态监控相关变量（用于去抖动和冷却）
        self.pending_issue = None
        self.issue_start_time = 0
        self.last_beep_time = 0

        # Type1 (轻度提示) 冷却机制
        self._toast_last_time_by_msg = {}
        self._toast_cooldown = 3.0

        # Type2 (重度弹窗) 控制机制
        self._type2_open = False
        self._type2_last_close_time = 0.0
        self._type2_reopen_delay = 2.0

        self.init_ui()
        self.apply_theme(self._theme_name)

        # 连接音量控制信号
        if hasattr(self.controls_panel, 'slider_vol'):
            self.controls_panel.slider_vol.valueChanged.connect(SoundMgr.set_volume)
            # 同步初始音量设置
            SoundMgr.set_volume(self.controls_panel.slider_vol.value())

    def apply_theme(self, name: str):
        """
        应用指定的主题。

        Args:
            name (str): 主题名称，如 'light' 或 'dark'。
        """
        self._theme_name = name
        self._theme = theme_by_name(name)

        # 更新背景和组件样式
        self.central_bg.set_background(self._theme.bg, self._theme.bg_image)
        self.right_sidebar.set_bg_image(self._theme.sidebar_bg_image)
        self.setStyleSheet(qss(self._theme))

        # 更新子组件主题
        self.toast.set_theme(self._theme_name)
        self.modal.set_theme(self._theme_name)

    def toggle_theme(self):
        # 在亮色和暗色主题之间切换
        self.apply_theme("dark" if self._theme_name == "light" else "light")

    def init_ui(self):
        """初始化用户界面布局及所有子组件。"""
        self.central_bg = BackgroundWidget()
        self.setCentralWidget(self.central_bg)

        root = QHBoxLayout(self.central_bg)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # 左侧区域 (视频 + 仪表盘)
        left_side = QWidget()
        left_layout = QVBoxLayout(left_side)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        self.video_frame = QFrame()
        self.video_frame.setObjectName("HeroCard")

        # 使用 StackedLayout 实现视频层与 Overlay 层的叠加
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

        # 添加视频区到左侧布局
        left_layout.addWidget(self.video_frame, stretch=7)

        # 初始化提示组件
        self.toast = ToastBubble(self.overlay)
        self.modal = ModalBubble()
        self.modal.closed.connect(self.on_modal_closed)

        # 底部监控仪表盘
        self.bottom_monitor = HorizontalMonitorBar()
        self.bottom_monitor.setFixedHeight(180)
        left_layout.addWidget(self.bottom_monitor, stretch=3)

        root.addWidget(left_side, 1)

        # 右侧侧边栏
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

        # 面板堆叠区
        self.stack = QStackedWidget()

        self.clock_panel = ClockPanel()
        self.todo_panel = ToDoPanel()  # 初始化待办面板
        self.controls_panel = ControlsPanel()

        # 按顺序添加：0=Clock, 1=Todo, 2=Controls
        self.stack.addWidget(self.clock_panel)
        self.stack.addWidget(self.todo_panel)
        self.stack.addWidget(self.controls_panel)

        content_layout.addWidget(self.stack, 1)

        root.addWidget(self.right_sidebar, 0)

        # 侧边工具栏，即面板切换按钮
        toolbar = QFrame()
        toolbar.setObjectName("Card")
        toolbar.setFixedWidth(68)

        t_lay = QVBoxLayout(toolbar)
        t_lay.setContentsMargins(10, 10, 10, 10)
        t_lay.setSpacing(10)

        # 创建所有功能按钮
        self.btn_clock = self._create_btn("⏰", lambda: self.stack.setCurrentIndex(0))
        self.btn_todo = self._create_btn("📝", lambda: self.stack.setCurrentIndex(1))
        self.btn_ctrl = self._create_btn("⚙️", lambda: self.stack.setCurrentIndex(2))
        self.btn_theme = self._create_btn("🌓", self.toggle_theme)
        self.btn_exit = self._create_btn("⏻", self.close_application)

        # 添加按钮，实现底部对齐
        t_lay.addStretch(1)
        t_lay.addWidget(self.btn_clock)
        t_lay.addWidget(self.btn_todo)
        t_lay.addWidget(self.btn_ctrl)
        t_lay.addWidget(self.btn_theme)
        t_lay.addWidget(self.btn_exit)

        root.addWidget(toolbar, 0)

    def _create_btn(self, icon: str, cb):
        """辅助函数：创建统一风格的工具栏按钮。"""
        btn = QPushButton(icon)
        btn.setObjectName("ToolBtn")
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(cb)
        return btn

    def _video_frame_global_rect(self) -> QRect:
        """获取视频区域的全局坐标矩形，用于定位模态弹窗。"""
        top_left = self.video_frame.mapToGlobal(self.video_frame.rect().topLeft())
        return QRect(top_left, self.video_frame.size())

    def on_modal_closed(self):
    
        # 重置冷却时间和状态，允许后续弹窗再次触发

        self._type2_open = False
        self._type2_last_close_time = time.time()

        self.pending_issue = None
        self.issue_start_time = 0

    def update_dashboard(self, data):
        """
        处理 AI 线程返回的数据。

        功能：
        1. 更新底部仪表盘显示。
        2. 执行业务逻辑判断（如疲劳检测、姿态检测）。
        3. 触发相应的视觉和声音警报。
        """
        if "Error" in data:
            return

        a, b, c = data.get("A", {}), data.get("B", {}), data.get("C", {})
        config = self.controls_panel.get_config()
        now = time.time()

        # 更新仪表盘数据
        self.bottom_monitor.update_data(a, b, c)

        issue_msg = None
        issue_level = 0

        # 检测 重度 违规
        if config["phone"] and c.get("手机使用", {}).get("使用手机"):
            issue_msg, issue_level = "禁止使用手机", 2
        elif config["away"] and c.get("离席检测", {}).get("离席"):
            issue_msg, issue_level = "检测到离席", 2

        # 检测 轻度 违规，仅在无重度违规时检测
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

        # 违规报警逻辑 (2秒持续时间确认)
        if issue_msg:
            if issue_msg != self.pending_issue:
                self.pending_issue = issue_msg
                self.issue_start_time = now

            if now - self.issue_start_time >= 2.0:
                self.show_alert(issue_msg, issue_level)

                # 声音提示 (4秒冷却)
                if now - self.last_beep_time > 4.0 and config["volume"] > 0:
                    sound_name = "alarm" if issue_level == 2 else "alert"
                    SoundMgr.play(sound_name)
                    self.last_beep_time = now
        else:
            self.pending_issue = None
            self.issue_start_time = 0

    def show_alert(self, msg, level):
        """显示视觉提示 (气泡或模态弹窗)。"""
        now = time.time()

        # Type2 (重度)
        if level == 2:
            if self._type2_open and self.modal.isVisible():
                self.modal.show_at(msg, self._video_frame_global_rect())
                return

            if (now - self._type2_last_close_time) < self._type2_reopen_delay:
                return

            self._type2_open = True
            self.modal.show_at(msg, self._video_frame_global_rect())
            return

        # Type1 (轻度)
        if self.modal.isVisible():
            return

        last_t = self._toast_last_time_by_msg.get(msg, 0.0)
        if (now - last_t) < self._toast_cooldown:
            return

        self._toast_last_time_by_msg[msg] = now
        self.toast.show_toast(msg, duration_ms=1200)
        self.toast.raise_()

    def start_worker(self):
        """启动 AI 处理线程。"""
        self.thread = AIWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_dashboard)
        self.thread.start()

    def update_image(self, cv_img):
        """刷新视频帧显示。"""
        h, w, ch = cv_img.shape
        qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

        # 保持 Overlay 层在视频上方
        self.overlay.raise_()
        if self.toast.isVisible():
            self.toast.raise_()

    def close_application(self):
        """显示退出确认弹窗。"""
        dlg = QuitDialog(self)
        if dlg.exec_() == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        """窗口关闭事件：确保 AI 线程被停止。"""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
        super().closeEvent(event)