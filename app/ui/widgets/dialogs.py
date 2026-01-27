from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

#此文件写了退出程序时的弹窗，提供缓冲，以免用户误触到退出程序
class QuitDialog(QMessageBox):

    def __init__(self, parent=None):
        """
        初始化退出确认弹窗。

        Args:
            parent: 父组件，用于弹窗居中显示。
        """
        super().__init__(parent)

        # 设置左上角标题
        self.setWindowTitle("温馨提示")

        # 去除左上角窗口图标
        self.setWindowIcon(QIcon())

        # 设置主文本
        self.setText("确定要退出程序吗？")

        # 去除内容区域的大图标
        self.setIcon(QMessageBox.NoIcon)

        # 设置按钮确定和取消
        self.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)

        btn_yes = self.button(QMessageBox.Yes)
        btn_yes.setText("确定")
        btn_yes.setObjectName("BtnPrimary")

        btn_no = self.button(QMessageBox.No)
        btn_no.setText("取消")
        btn_no.setObjectName("BtnSecondary")

        # 核心逻辑：强制按钮居中
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            button_box.setCenterButtons(True)

        # 应用美化样式
        self._apply_stylesheet()

    def _apply_stylesheet(self):
        """应用 QSS 样式表"""
        self.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px; /* 弹窗保持圆角 */
            }
            QLabel {
                color: #1F2A37;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                padding: 20px 40px; /* 增加内边距 */
                min-width: 200px;   /* 保证弹窗宽度 */
                qproperty-alignment: AlignCenter; /* 文字居中 */
            }
            
            /* 按钮通用样式，方形框设计 */
            QPushButton {
                border-radius: 4px; /* 微圆角 */
                padding: 8px 30px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
                margin: 0 10px; /* 按钮之间的间距 */
            }

            /* 确定按钮 (蓝色实心框) */
            QPushButton#BtnPrimary {
                background-color: #3B82C4;
                color: #FFFFFF;
                border: 1px solid #2E6DA4; /* 深色边框 */
            }
            QPushButton#BtnPrimary:hover {
                background-color: #3272B0;
            }

            /* 取消按钮 */
            QPushButton#BtnSecondary {
                background-color: #FFFFFF; /* 白底 */
                color: #4B5563;
                border: 1px solid #9CA3AF; /* 灰色边框 */
            }
            QPushButton#BtnSecondary:hover {
                background-color: #F3F4F6;
                border-color: #6B7280;
                color: #1F2A37;
            }
        """)