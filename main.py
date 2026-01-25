import sys
import os
import traceback
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def clean_logs():
    for f in ["posture_results.jsonl", "behavior_results.json", "attention_output.jsonl", "monitor.log"]:
        p = project_root / f
        if p.exists():
            try: os.remove(p)
            except: pass

from app.ui.main_window import MainWindow

# 手写皮肤样式 (略) - 保持之前的 DARK_THEME_STYLESHEET 不变
DARK_THEME_STYLESHEET = """
QWidget { font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; }
QToolTip { border: 1px solid #555; background-color: #1e1e1e; color: #fff; padding: 5px; }
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget { background: transparent; }
QCheckBox { spacing: 8px; color: #ccc; font-size: 14px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #666; border-radius: 4px; background: #2b2b2b; }
QCheckBox::indicator:hover { border: 1px solid #00e5ff; }
QCheckBox::indicator:checked { background: #00e5ff; border: 1px solid #00e5ff; }
QSlider::groove:horizontal { border: 1px solid #333; height: 6px; background: #2b2b2b; margin: 2px 0; border-radius: 3px; }
QSlider::handle:horizontal { background: #00e5ff; border: 1px solid #00e5ff; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }
QScrollBar:vertical { border: none; background: #1a1a1a; width: 8px; margin: 0px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #00e5ff; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QProgressBar { border: none; background-color: #2b2b2b; border-radius: 4px; text-align: center; color: white; font-weight: bold; }
QProgressBar::chunk { background-color: #00e676; border-radius: 4px; }
"""

if __name__ == "__main__":
    try:
        clean_logs()
        print("🚀 正在启动 SmartStudy Monitor (Stable Ver)...")
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        
        app = QApplication(sys.argv)
        app.setStyleSheet(DARK_THEME_STYLESHEET)

        win = MainWindow()
        win.show()
        
        QTimer.singleShot(1000, win.start_worker)
        
        sys.exit(app.exec_())
    
    except Exception as e:
        print("❌ 程序发生致命错误:")
        traceback.print_exc()
        # 如果是图形界面还没启动就崩了，尝试弹窗（可选）
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(e), "启动失败", 16)
        except: pass
        input("按回车键退出...")