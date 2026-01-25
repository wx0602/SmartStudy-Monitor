from PyQt5.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
                             QCheckBox, QTimeEdit, QSlider, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont

class ClockPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; color: #e0e0e0;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 0)
        
        title = QLabel("时间管理终端")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #888; margin-bottom: 10px;")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea {background: transparent;} QScrollBar:vertical {width:6px; background:transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        
        # 关键修改：content_layout
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(15, 0, 15, 20)
        self.content_layout.setSpacing(15)
        
        self.create_digital_clock_card()
        self.create_alarm_card()
        self.create_focus_card()
        self.content_layout.addStretch() 
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_time)
        self.timer.start(1000)

    def create_card_frame(self, title):
        frame = QFrame()
        frame.setStyleSheet("background: #252525; border-radius: 8px; padding: 12px; border: 1px solid #333;")
        vbox = QVBoxLayout(frame)
        lbl = QLabel(title)
        lbl.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        lbl.setStyleSheet("color: #aaa; padding-bottom: 8px; border-bottom: 1px solid #444;")
        vbox.addWidget(lbl)
        
        # 使用 content_layout
        self.content_layout.addWidget(frame)
        return vbox, frame

    def create_digital_clock_card(self):
        frame = QFrame()
        frame.setStyleSheet("background: #1a1a1a; border-radius: 12px; border: 1px solid #333; padding: 20px;")
        vbox = QVBoxLayout(frame)
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setStyleSheet("font-size: 48px; font-weight: bold; color: #00e5ff; font-family: 'Consolas';")
        self.lbl_date = QLabel("YYYY-MM-DD")
        self.lbl_date.setAlignment(Qt.AlignCenter)
        self.lbl_date.setStyleSheet("font-size: 14px; color: #666; margin-top: -5px;")
        vbox.addWidget(self.lbl_time)
        vbox.addWidget(self.lbl_date)
        
        # 使用 content_layout
        self.content_layout.addWidget(frame)

    def create_alarm_card(self):
        vbox, _ = self.create_card_frame("⏰ 闹钟设置")
        
        row_sw = QHBoxLayout()
        self.cb_alarm = QCheckBox("启用提醒")
        row_sw.addWidget(self.cb_alarm)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime().addSecs(3600))
        self.time_edit.setStyleSheet("QTimeEdit { background: #333; color: white; border: 1px solid #555; font-size: 18px; padding: 5px; border-radius: 6px; }")
        self.time_edit.setAlignment(Qt.AlignCenter)
        row_sw.addWidget(self.time_edit)
        vbox.addLayout(row_sw)
        
        vbox.addSpacing(10)
        row_vol = QHBoxLayout()
        lbl_vol = QLabel("提示音量")
        lbl_vol.setStyleSheet("color: #888;")
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100); self.slider_vol.setValue(80)
        self.slider_vol.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #444; border-radius: 2px; } QSlider::handle:horizontal { background: #ff9800; width: 16px; margin: -6px 0; border-radius: 8px; }")
        row_vol.addWidget(lbl_vol); row_vol.addWidget(self.slider_vol)
        vbox.addLayout(row_vol)

    def create_focus_card(self):
        vbox, _ = self.create_card_frame("🍅 专注模式 (Beta)")
        desc = QLabel("即将上线：\n番茄钟计时与强制锁屏功能")
        desc.setStyleSheet("color: #555; font-style: italic; font-size: 12px;")
        desc.setAlignment(Qt.AlignCenter)
        vbox.addWidget(desc)

    def refresh_time(self):
        from PyQt5.QtCore import QDate
        self.lbl_time.setText(QTime.currentTime().toString("HH:mm:ss"))
        self.lbl_date.setText(QDate.currentDate().toString("yyyy-MM-dd dddd"))

    def get_settings(self):
        return { "is_on": self.cb_alarm.isChecked(), "target_time": self.time_edit.time(), "volume": self.slider_vol.value() }