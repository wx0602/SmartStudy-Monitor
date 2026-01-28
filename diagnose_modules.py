#此程序用于测试各个手写包能否成功导入，如果程序无法运行请运行此程序，查看是否存在没有成功导入的包
import sys
import os
import traceback
from pathlib import Path

# 1. 确保能找到 app 目录
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

print("🔍 开始深度模块诊断...")
print(f"📂 项目根目录: {project_root}")

def test_module(name):
    print(f"\n--------------------------------")
    print(f"👉 正在尝试导入: {name}")
    try:
        __import__(name)
        print(f"{name} 导入成功")
    except ImportError as e:
        print(f"{name} 导入失败 (ImportError)")
        print(f"   原因: {e}")
    except Exception as e:
        print(f"{name} 发生运行时错误 (CRITICAL)")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误详情: {str(e)}")
        print("  错误堆栈:")
        traceback.print_exc()

# 第一阶段：基础 UI 组件
test_module("app.ui.clock") 

test_module("app.ui.dashboard_modules.focus_card")
test_module("app.ui.dashboard_modules.behavior_card")

# 第二阶段：核心功能 (Detector)
# 这里通常涉及 YOLO 和 Mediapipe 的初始化
test_module("app.core.detector") 

# 第三阶段：主窗口
test_module("app.ui.main_window")

print("\n--------------------------------")
print("诊断结束。请把上面的红色报错信息发给我！")
input("按回车退出...")