import sys
import os
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt

# 1. 环境配置
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from app.ui.main_window import MainWindow

# === 现代简约浅色主题 (Light Theme) ===
LIGHT_THEME_STYLESHEET = """
QWidget { 
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; 
    background-color: #f4f5f7;  /* 整体背景：淡灰 */
    color: #333333;             /* 全局文字：深灰 */
}

/* 强制隐藏横向滚动条 */
QScrollBar:horizontal { height: 0px; }

/* 纵向滚动条：浅色极简 */
QScrollBar:vertical { 
    border: none; 
    background: #e9ecef; 
    width: 8px; 
    border-radius: 4px; 
}
QScrollBar::handle:vertical { 
    background: #ced4da; 
    min-height: 20px; 
    border-radius: 4px; 
}
QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

/* 按钮样式：白底灰边 */
QPushButton { 
    background-color: #ffffff;
    border: 1px solid #dcdcdc;
    border-radius: 6px; 
    color: #333;
}
QPushButton:hover {
    background-color: #e9ecef;
    border-color: #c0c0c0;
}

/* 进度条：浅灰槽 */
QProgressBar { 
    border: none; 
    background-color: #e9ecef; 
    border-radius: 3px; 
}
QProgressBar::chunk { 
    background-color: #28a745; /* 标准绿 */
}

/* 输入框与下拉框 */
QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px;
    color: #333;
}
"""

def clean_temp_files():
    temp_files = ["monitor.log", "attention_output.jsonl", "behavior_results.json"]
    for f in temp_files:
        p = project_root / f
        if p.exists():
            try: os.remove(p)
            except: pass

if __name__ == "__main__":
    try:
        clean_temp_files()
        print("🚀 SmartStudy Monitor (Light Mode) 正在启动...")
        
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setStyleSheet(LIGHT_THEME_STYLESHEET)

        win = MainWindow()
        win.show()
        
        QTimer.singleShot(1000, win.start_worker)
        sys.exit(app.exec_())
    
    except Exception:
        print("❌ 程序启动发生致命错误:")
        traceback.print_exc()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "启动失败，请检查控制台输出。", "错误", 16)
        except:
            pass
        input("\n按回车键退出程序...")