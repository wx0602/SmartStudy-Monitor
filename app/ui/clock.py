from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QLabel, QTimeEdit, 
                             QPushButton, QHBoxLayout, QSpinBox, QStackedWidget, QWidget)
from PyQt5.QtCore import QTimer, QTime, QDate, Qt
import winsound

class ClockPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame { 
                background: #ffffff; 
                border-radius: 12px; 
                border: 1px solid #e0e0e0; 
            }
            QLabel { border: none; background: transparent; color: #333; }
            
            /* 容器背景 */
            QFrame#Container {
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #eee;
            }

            /* 按钮通用风格 */
            QPushButton {
                border-radius: 16px; /* 32px 的一半 */
                font-weight: bold;
                font-size: 11px;
            }
            
            /* 绿色按钮 (开始) */
            QPushButton#BtnStart {
                background-color: #e3f9e5; color: #28a745; border: 1px solid #28a745;
            }
            QPushButton#BtnStart:hover { background-color: #d4edda; }
            
            /* 黄色按钮 (暂停) */
            QPushButton#BtnPause {
                background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;
            }
            
            /* 灰色按钮 (复位) */
            QPushButton#BtnReset {
                background-color: #e9ecef; color: #495057; border: 1px solid #ced4da;
            }

            /* 闹钟开关大按钮 */
            QPushButton#BtnAlarmToggle {
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#BtnAlarmToggle:checked {
                background-color: #007bff; color: white; border: none;
            }
            
            /* 核心修改：输入框完全透明化，去边框 */
            QSpinBox {
                background: transparent;
                border: none;
                font-weight: bold;
            }
            /* 去掉输入框选中时的背景色，防止出现蓝色方块 */
            QSpinBox::selection {
                background: transparent;
                color: #000;
            }
        """)
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
        layout.setSpacing(5) 

        # === 1. 主时钟区 (顶部) ===
        self.lbl_title = QLabel("当前时间")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(self.lbl_title)

        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setStyleSheet("color: #333; font-size: 42px; font-family: 'Consolas'; font-weight: bold;")
        layout.addWidget(self.lbl_time)

        self.lbl_date = QLabel("YYYY-MM-DD")
        self.lbl_date.setAlignment(Qt.AlignCenter)
        self.lbl_date.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(self.lbl_date)
        
        # 间距
        layout.addSpacing(25)
        
        # === 2. 闹钟模块 ===
        alarm_box = QFrame()
        alarm_box.setObjectName("Container")
        # 保持原有大小
        v_alarm = QVBoxLayout(alarm_box)
        v_alarm.setContentsMargins(10, 15, 10, 15)
        v_alarm.setSpacing(10)
        
        lbl_a_title = QLabel("每日闹钟")
        lbl_a_title.setAlignment(Qt.AlignCenter)
        lbl_a_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        v_alarm.addWidget(lbl_a_title)
        
        h_alarm_ctrl = QHBoxLayout()
        h_alarm_ctrl.addStretch() 
        
        self.alarm_time = QTimeEdit()
        self.alarm_time.setDisplayFormat("HH:mm")
        self.alarm_time.setTime(QTime.currentTime().addSecs(60))
        self.alarm_time.setStyleSheet("font-size: 26px; color: #333; background: transparent; border: none; font-weight: bold;")
        self.alarm_time.setFixedWidth(115) 
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

        # 模块间距
        layout.addSpacing(15) 

        # === 3. 计时器模块 (核心修复) ===
        timer_box = QFrame()
        timer_box.setObjectName("Container")
        
        # 关键修改1：强制固定高度 115px，防止被拉伸出现大片空白
        timer_box.setFixedHeight(130) 
        
        v_timer = QVBoxLayout(timer_box)
        # 关键修改2：边距调整，让内容垂直居中且紧凑
        v_timer.setContentsMargins(5, 12, 5, 12) 
        v_timer.setSpacing(5)
        
        # [第一行] 标题居中
        lbl_t_title = QLabel("计时器")
        lbl_t_title.setAlignment(Qt.AlignCenter)
        lbl_t_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        v_timer.addWidget(lbl_t_title)

        # [第二行] 显示区
        self.stack_display = QStackedWidget()
        self.stack_display.setFixedHeight(40)
        
        # 页面0: 设定时间
        self.spin_min = QSpinBox()
        self.spin_min.setRange(1, 180)
        self.spin_min.setValue(25)
        self.spin_min.setSuffix(" 分钟")
        self.spin_min.setAlignment(Qt.AlignCenter)
        # 字体颜色纯黑，背景透明
        self.spin_min.setStyleSheet("QSpinBox { font-size: 34px; color: #000000; background: transparent; border:none; font-weight: bold; }")
        self.stack_display.addWidget(self.spin_min)
        
        # 页面1: 倒数显示
        self.lbl_countdown = QLabel("25:00")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        self.lbl_countdown.setStyleSheet("font-size: 34px; font-family: 'Consolas'; color: #000000; font-weight: bold;")
        self.stack_display.addWidget(self.lbl_countdown)
        
        v_timer.addWidget(self.stack_display)
        
        # [第三行] 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20) # 按钮拉开一点距离
        
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
        # 1. 主时钟
        t = QTime.currentTime()
        self.lbl_time.setText(t.toString("HH:mm:ss"))
        week_map = {1:"一", 2:"二", 3:"三", 4:"四", 5:"五", 6:"六", 7:"日"}
        self.lbl_date.setText(f"{QDate.currentDate().toString('yyyy-MM-dd')} 星期{week_map.get(QDate.currentDate().dayOfWeek(), '')}")

        # 2. 闹钟
        if self.alarm_active:
            target = self.alarm_time.time()
            if t.hour() == target.hour() and t.minute() == target.minute() and t.second() == 0:
                self.trigger_alert("⏰ 闹钟响铃！")

        # 3. 倒计时
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
        if self.countdown_state == "STOPPED":
            self.btn_reset.setEnabled(False)
            self.btn_reset.setStyleSheet("background-color: #f1f3f5; color: #adb5bd; border:none;")
        else:
            self.btn_reset.setEnabled(True)
            self.btn_reset.setStyleSheet("background-color: #e9ecef; color: #495057; border:1px solid #ced4da;")

        if self.countdown_state == "RUNNING":
            self.btn_start.setText("暂停")
            self.btn_start.setObjectName("BtnPause")
            self.btn_start.setStyleSheet("background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;")
        else:
            txt = "继续" if self.countdown_state == "PAUSED" else "启动"
            self.btn_start.setText(txt)
            self.btn_start.setObjectName("BtnStart")
            self.btn_start.setStyleSheet("background-color: #e3f9e5; color: #28a745; border: 1px solid #28a745;")

    def update_lcd_display(self):
        m, s = divmod(self.remaining_seconds, 60)
        self.lbl_countdown.setText(f"{m:02d}:{s:02d}")

    def trigger_alert(self, msg):
        winsound.Beep(1000, 800)
        print(msg)