# 此程序用于诊断环境依赖模块是否成功导入，如果环境出问题可直接运行此模块
import sys
import time

print("--- 诊断开始 ---")
sys.stdout.flush()

print("1. 正在测试 PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow
    print("   ✅ PyQt5 导入成功")
except Exception as e:
    print(f"   ❌ PyQt5 挂了: {e}")
sys.stdout.flush()

print("2. 正在测试 Numpy...")
try:
    import numpy
    print(f"   ✅ Numpy 导入成功 (版本: {numpy.__version__})")
except Exception as e:
    print(f"   ❌ Numpy 挂了: {e}")
sys.stdout.flush()

print("3. 正在测试 OpenCV (这步最容易卡)...")
try:
    import cv2
    print(f"   ✅ OpenCV 导入成功 (版本: {cv2.__version__})")
except Exception as e:
    print(f"   ❌ OpenCV 挂了: {e}")
sys.stdout.flush()

print("4. 正在测试 Mediapipe...")
try:
    import mediapipe
    print("   ✅ Mediapipe 导入成功")
except Exception as e:
    print(f"   ❌ Mediapipe 挂了: {e}")
sys.stdout.flush()

print("5. 正在测试 Ultralytics (YOLO)...")
try:
    from ultralytics import YOLO
    print("   ✅ YOLO 导入成功")
except Exception as e:
    print(f"   ❌ YOLO 挂了: {e}")
sys.stdout.flush()

print("--- 诊断结束 ---")
input("按回车键退出...")