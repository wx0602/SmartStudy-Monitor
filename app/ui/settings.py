from PyQt5.QtWidgets import QDialog, QFormLayout, QCheckBox, QSlider, QDialogButtonBox
from PyQt5.QtCore import Qt

# 系统设置弹窗
# 功能：模态对话框，用于调节全局功能的开关
class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 监测设置")
        self.setFixedSize(300, 200)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        layout = QFormLayout(self)
        
        # 选项1：AI 提示总开关
        self.cb_enable = QCheckBox("开启 AI 行为纠正提示")
        self.cb_enable.setChecked(current_settings.get("enable_alerts", True))
        layout.addRow(self.cb_enable)

        # 选项2：AI 提示音量
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(current_settings.get("ai_volume", 50))
        layout.addRow("AI 提示音量:", self.slider_vol)

        # 确认/取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept) # 点击确定 -> 触发 accept()
        buttons.rejected.connect(self.reject) # 点击取消 -> 触发 reject()
        layout.addRow(buttons)
        
        # 保存一份当前设置的副本，防止修改被取消
        self.result_settings = current_settings.copy()
        
    # 重写 accept 方法，点击“确定”时保存用户修改的值
    def accept(self):
        self.result_settings["enable_alerts"] = self.cb_enable.isChecked()
        self.result_settings["ai_volume"] = self.slider_vol.value()
        super().accept()