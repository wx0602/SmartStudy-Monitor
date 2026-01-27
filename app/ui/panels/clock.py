from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTimeEdit,
    QPushButton, QHBoxLayout, QSpinBox, QStackedWidget
)
from PyQt5.QtCore import QTimer, QTime, QDate, Qt

from app.audio_manager import SoundMgr


class ClockPanel(QFrame):
    """
    时钟面板组件:
    1. 当前日期和时间显示
    2. 每日定点闹钟
    3. 专注倒计时器
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置对象名称以应用 QSS 样式 (卡片外观)
        self.setObjectName("Card")
        self.setMinimumWidth(0)

        # 状态变量初始化
        self.alarm_active = False
        self.countdown_state = "STOPPED"  # 可选值: STOPPED, RUNNING, PAUSED
        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds

        self.init_ui()

        # 启动主定时器，每秒触发一次更新循环
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)

        # 第一部分：主时间显示
        self.lbl_title = QLabel("当前时间")
        self.lbl_title.setObjectName("ClockTitle")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setObjectName("ClockTime")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_time)

        self.lbl_date = QLabel("YYYY-MM-DD")
        self.lbl_date.setObjectName("ClockDate")
        self.lbl_date.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_date)

        layout.addSpacing(18)

        # 第二部分：每日闹钟
        alarm_box = QFrame()
        alarm_box.setObjectName("Container")
        
        v_alarm = QVBoxLayout(alarm_box)
        v_alarm.setContentsMargins(12, 14, 12, 14)
        v_alarm.setSpacing(10)

        lbl_a_title = QLabel("每日闹钟")
        lbl_a_title.setObjectName("Title")
        lbl_a_title.setAlignment(Qt.AlignCenter)
        v_alarm.addWidget(lbl_a_title)

        h_alarm_ctrl = QHBoxLayout()
        h_alarm_ctrl.addStretch()

        # 时间选择控件
        self.alarm_time = QTimeEdit()
        self.alarm_time.setDisplayFormat("HH:mm")
        # 默认设置为当前时间的一分钟后，方便测试
        self.alarm_time.setTime(QTime.currentTime().addSecs(60))
        self.alarm_time.setFixedWidth(120)
        h_alarm_ctrl.addWidget(self.alarm_time)

        # 开关按钮
        self.btn_alarm_toggle = QPushButton("OFF")
        self.btn_alarm_toggle.setObjectName("BtnAlarmToggle")
        self.btn_alarm_toggle.setCheckable(True)
        self.btn_alarm_toggle.setFixedSize(60, 34)
        self.btn_alarm_toggle.clicked.connect(self.toggle_alarm)
        h_alarm_ctrl.addWidget(self.btn_alarm_toggle)

        h_alarm_ctrl.addStretch()
        v_alarm.addLayout(h_alarm_ctrl)

        layout.addWidget(alarm_box)
        layout.addSpacing(12)

        # 第三部分：倒计时器
        timer_box = QFrame()
        timer_box.setObjectName("Container")
        timer_box.setFixedHeight(140)

        v_timer = QVBoxLayout(timer_box)
        v_timer.setContentsMargins(10, 12, 10, 12)
        v_timer.setSpacing(8)

        lbl_t_title = QLabel("计时器")
        lbl_t_title.setObjectName("Title")
        lbl_t_title.setAlignment(Qt.AlignCenter)
        v_timer.addWidget(lbl_t_title)

        # 使用 StackedWidget 在“设置模式”和“运行模式”之间切换
        self.stack_display = QStackedWidget()
        self.stack_display.setFixedHeight(42)

        # 页面 0: 设置分钟数 (QSpinBox)
        self.spin_min = QSpinBox()
        self.spin_min.setRange(1, 180)
        self.spin_min.setValue(25)
        self.spin_min.setSuffix(" 分钟")
        self.spin_min.setAlignment(Qt.AlignCenter)
        self.spin_min.setStyleSheet("font-size: 34px; font-weight: 1000;")
        self.stack_display.addWidget(self.spin_min)

        # 页面 1: 倒计时数字显示 (QLabel)
        self.lbl_countdown = QLabel("25:00")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        self.lbl_countdown.setStyleSheet(
            "font-size: 34px; font-family: 'Consolas'; font-weight: 1000;"
        )
        self.stack_display.addWidget(self.lbl_countdown)

        v_timer.addWidget(self.stack_display)

        # 底部按钮组
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.btn_reset = QPushButton("复位")
        self.btn_reset.setObjectName("BtnReset")
        self.btn_reset.setFixedSize(32, 32)
        self.btn_reset.clicked.connect(self.reset_timer)
        self.btn_reset.setEnabled(False)

        self.btn_start = QPushButton("启动")
        self.btn_start.setObjectName("BtnStart")
        self.btn_start.setFixedSize(32, 32)
        self.btn_start.clicked.connect(self.toggle_timer)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addStretch()

        v_timer.addLayout(btn_layout)
        layout.addWidget(timer_box)

        layout.addStretch()

    def update_loop(self):
        """主更新循环：刷新时间显示，检查闹钟与倒计时状态。"""
        t = QTime.currentTime()
        self.lbl_time.setText(t.toString("HH:mm:ss"))
        
        # 星期映射表
        week_map = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
        d = QDate.currentDate()
        self.lbl_date.setText(
            f"{d.toString('yyyy-MM-dd')} 星期{week_map.get(d.dayOfWeek(), '')}"
        )

        # 检查每日闹钟
        if self.alarm_active:
            target = self.alarm_time.time()
            # 仅在时、分匹配且秒为 0 时触发
            if (t.hour() == target.hour() and 
                t.minute() == target.minute() and 
                t.second() == 0):
                self.trigger_alert("⏰ 闹钟响铃！")

        # 更新倒计时逻辑
        if self.countdown_state == "RUNNING":
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.update_lcd_display()
            else:
                self.countdown_state = "STOPPED"
                self.update_btn_ui()
                self.trigger_alert("⏳ 计时结束！")

    def toggle_alarm(self):
        """切换闹钟的激活状态。"""
        if self.btn_alarm_toggle.isChecked():
            self.alarm_active = True
            self.btn_alarm_toggle.setText("ON")
            self.alarm_time.setEnabled(False)
        else:
            self.alarm_active = False
            self.btn_alarm_toggle.setText("OFF")
            self.alarm_time.setEnabled(True)

    def toggle_timer(self):
        """处理计时器主按钮点击 (启动/暂停/继续)。"""
        if self.countdown_state == "STOPPED":
            # 从停止状态开始：读取设定时间
            self.total_seconds = self.spin_min.value() * 60
            self.remaining_seconds = self.total_seconds
            self.countdown_state = "RUNNING"
            self.update_lcd_display()
            self.stack_display.setCurrentIndex(1)
        elif self.countdown_state == "RUNNING":
            # 运行中 -> 暂停
            self.countdown_state = "PAUSED"
        elif self.countdown_state == "PAUSED":
            # 暂停中 -> 继续
            self.countdown_state = "RUNNING"

        self.update_btn_ui()

    def reset_timer(self):
        """重置计时器到初始状态。"""
        self.countdown_state = "STOPPED"
        self.remaining_seconds = self.total_seconds
        self.stack_display.setCurrentIndex(0)
        self.update_btn_ui()

    def update_btn_ui(self):
        """根据当前状态更新按钮的文本和样式。"""
        self.btn_reset.setEnabled(self.countdown_state != "STOPPED")

        if self.countdown_state == "RUNNING":
            self.btn_start.setText("暂停")
            self.btn_start.setObjectName("BtnPause")
        else:
            is_paused = (self.countdown_state == "PAUSED")
            self.btn_start.setText("继续" if is_paused else "启动")
            self.btn_start.setObjectName("BtnStart")

        # 刷新样式以应用新的 objectName
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)
        self.btn_start.update()

    def update_lcd_display(self):
        """将剩余秒数格式化为 MM:SS 并显示。"""
        m, s = divmod(self.remaining_seconds, 60)
        self.lbl_countdown.setText(f"{m:02d}:{s:02d}")

    def trigger_alert(self, msg):
        """
        触发提醒。
        
        使用 'timer' 专用音效，区别于系统警告声。
        """
        SoundMgr.play("timer")
        print(msg)