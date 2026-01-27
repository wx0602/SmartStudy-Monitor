import winsound
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTimeEdit,
    QPushButton, QHBoxLayout, QSpinBox, QStackedWidget
)
from PyQt5.QtCore import QTimer, QTime, QDate, Qt


class ClockPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ✅ 外层交给主题
        self.setObjectName("Card")
        self.setMinimumWidth(0)

        # 状态变量
        self.alarm_active = False
        self.countdown_state = "STOPPED"
        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)

        # 主时钟区
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

        # === 闹钟模块 ===
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

        self.alarm_time = QTimeEdit()
        self.alarm_time.setDisplayFormat("HH:mm")
        self.alarm_time.setTime(QTime.currentTime().addSecs(60))
        self.alarm_time.setFixedWidth(120)
        h_alarm_ctrl.addWidget(self.alarm_time)

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

        # === 计时器模块 ===
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

        self.stack_display = QStackedWidget()
        self.stack_display.setFixedHeight(42)

        # 页面0：设置分钟
        self.spin_min = QSpinBox()
        self.spin_min.setRange(1, 180)
        self.spin_min.setValue(25)
        self.spin_min.setSuffix(" 分钟")
        self.spin_min.setAlignment(Qt.AlignCenter)
        self.spin_min.setStyleSheet("font-size: 34px; font-weight: 1000;")  # 不写颜色
        self.stack_display.addWidget(self.spin_min)

        # 页面1：倒计时显示
        self.lbl_countdown = QLabel("25:00")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        self.lbl_countdown.setStyleSheet("font-size: 34px; font-family: 'Consolas'; font-weight: 1000;")
        self.stack_display.addWidget(self.lbl_countdown)

        v_timer.addWidget(self.stack_display)

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
        t = QTime.currentTime()
        self.lbl_time.setText(t.toString("HH:mm:ss"))
        week_map = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
        d = QDate.currentDate()
        self.lbl_date.setText(f"{d.toString('yyyy-MM-dd')} 星期{week_map.get(d.dayOfWeek(), '')}")

        # 闹钟
        if self.alarm_active:
            target = self.alarm_time.time()
            if t.hour() == target.hour() and t.minute() == target.minute() and t.second() == 0:
                self.trigger_alert("⏰ 闹钟响铃！")

        # 倒计时
        if self.countdown_state == "RUNNING":
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.update_lcd_display()
            else:
                self.countdown_state = "STOPPED"
                self.update_btn_ui()
                self.trigger_alert("⏳ 计时结束！")

    def toggle_alarm(self):
        if self.btn_alarm_toggle.isChecked():
            self.alarm_active = True
            self.btn_alarm_toggle.setText("ON")
            self.alarm_time.setEnabled(False)
        else:
            self.alarm_active = False
            self.btn_alarm_toggle.setText("OFF")
            self.alarm_time.setEnabled(True)

    def toggle_timer(self):
        if self.countdown_state == "STOPPED":
            self.total_seconds = self.spin_min.value() * 60
            self.remaining_seconds = self.total_seconds
            self.countdown_state = "RUNNING"
            self.update_lcd_display()
            self.stack_display.setCurrentIndex(1)
        elif self.countdown_state == "RUNNING":
            self.countdown_state = "PAUSED"
        elif self.countdown_state == "PAUSED":
            self.countdown_state = "RUNNING"

        self.update_btn_ui()

    def reset_timer(self):
        self.countdown_state = "STOPPED"
        self.remaining_seconds = self.total_seconds
        self.stack_display.setCurrentIndex(0)
        self.update_btn_ui()

    def update_btn_ui(self):
        self.btn_reset.setEnabled(self.countdown_state != "STOPPED")

        if self.countdown_state == "RUNNING":
            self.btn_start.setText("暂停")
            self.btn_start.setObjectName("BtnPause")
        else:
            self.btn_start.setText("继续" if self.countdown_state == "PAUSED" else "启动")
            self.btn_start.setObjectName("BtnStart")

        # 关键：切换 objectName 后刷新样式
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)
        self.btn_start.update()

    def update_lcd_display(self):
        m, s = divmod(self.remaining_seconds, 60)
        self.lbl_countdown.setText(f"{m:02d}:{s:02d}")

    def trigger_alert(self, msg):
        winsound.Beep(1000, 800)
        print(msg)
