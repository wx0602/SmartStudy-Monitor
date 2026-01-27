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

def clean_temp_files():
    temp_files = ["monitor.log", "attention_output.jsonl", "behavior_results.json"]
    for f in temp_files:
        p = project_root / f
        if p.exists():
            try:
                os.remove(p)
            except:
                pass

if __name__ == "__main__":
    # 强制启用高分屏支持 (必须在创建 QApplication 之前)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)  # 先创建 App

    try:
        clean_temp_files()
        print("🚀 SmartStudy Monitor 正在启动...")
        print("1. 正在延迟加载主窗口模块 (关键步骤)...")
        from app.ui.main_window import MainWindow
        print("   ✅ 模块导入成功！")

        print("2. 正在初始化窗口...")
        win = MainWindow()

        # ✅ 主题由 MainWindow 统一管理（需要你在 MainWindow 中实现 apply_theme）
        # 默认启用明色；你也可以改成读取配置文件
        if hasattr(win, "apply_theme"):
            win.apply_theme("light")

        win.show()
        print("   ✅ 窗口显示成功！")

        # 延迟启动 AIWorker，避免启动卡顿
        QTimer.singleShot(1000, win.start_worker)

        print("3. 进入事件循环...")
        sys.exit(app.exec_())

    except ImportError as e:
        print("\n❌ 【致命错误】导入模块失败！")
        print(f"原因: {e}")
        print("请检查：1. 依赖库是否完整 2. 文件路径是否正确")
        traceback.print_exc()
        input("按回车键退出...")

    except Exception:
        print("\n❌ 【运行时错误】程序崩溃！")
        traceback.print_exc()
        input("按回车键退出...")
