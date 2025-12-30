# test_posture.py
import cv2
import time
# 导入你写的模块
from modules.posture.detector import PostureDetector


def main():
    # 1. 模拟一个配置字典 (假装是从 yaml 读取的)
    # 这样你就不用管文件读取的问题，专注于测试算法
    fake_config = {
        'posture': {
            'hunchback_angle_threshold': 150,  # 驼背阈值
            'head_forward_threshold': 0.35,    # 前伸比例
            'shoulder_tilt_angle': 5,          # 歪头角度
            'max_shoulder_width_ratio': 0.5,   # 距离过近
            'head_forward_z_threshold': 2.0,   # 头部前伸Z轴阈值
            'hunchback_ratio_threshold': 0.25  # 驼背颈部比例阈值
        }
    }

    # 2. 初始化你的检测器
    print("正在初始化检测器...")
    try:
        detector = PostureDetector(fake_config)
    except Exception as e:
        print(f"初始化失败，请检查 detector.py 的 __init__: {e}")
        return

    # 3. 打开摄像头 (0通常是默认摄像头)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头！")
        return

    print("开始测试... 按 'q' 键退出")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 记录开始时间算帧率
        start_time = time.time()

        # === 核心：调用你的 process_frame 函数 ===
        try:
            result = detector.process_frame(frame)
        except Exception as e:
            print(f"运行出错: {e}")
            break

        # === 可视化：把结果写在画面上 ===
        y_pos = 30
        for key, value in result.items():
            # 跳过 landmarks 数据，不然屏幕会被数字刷屏
            if key == "landmarks": 
                continue
            
            text = f"{key}: {value}"
            
            # 如果是 True (比如驼背了)，用红色显示，否则绿色
            color = (0, 0, 255) if value is True or value == "too_close" else (0, 255, 0)
            
            cv2.putText(frame, text, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_pos += 30


        # 显示画面
        cv2.imshow('Posture Test (Press q to exit)', frame)

        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()