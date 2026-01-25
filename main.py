import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 1. 设置根路径 (确保能找到 modules 和 app)
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 2. 导入主窗口
from app.window import MainWindow

if __name__ == "__main__":
    print("🚀 正在启动 SmartStudy Monitor...")
    
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    
    # 延迟 1 秒启动 AI，防止界面未渲染完成导致卡顿
    QTimer.singleShot(1000, win.start_worker)
    
    sys.exit(app.exec_())