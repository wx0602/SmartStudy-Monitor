import sys
import time
import json
from pathlib import Path

# 设置路径
print("[Debug] 正在设置环境路径...")
FILE_PATH = Path(__file__).resolve()
ROOT_DIR = FILE_PATH.parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
print(f"[Debug] 项目根目录: {ROOT_DIR}")

# 导入与诊断
print("[Debug] 正在导入依赖库...")
try:
    import cv2
    import mediapipe as mp
    # 关键诊断信息
    print(f"[Debug] MediaPipe 安装路径: {mp.__file__}")
    if not hasattr(mp, 'solutions'):
        print("[Fatal Error] MediaPipe 库损坏：找不到 solutions 属性！")
        print(">> 请尝试运行: pip install mediapipe==0.10.9")
        sys.exit(1)
    from modules.posture.detector import PostureDetector
    print("[Debug] 所有模块导入成功！")
except ImportError as e:
    print(f"[Error] 导入失败: {e}")
    sys.exit(1)

OUTPUT_FILE = ROOT_DIR / "posture_results.jsonl"

def main():
    print("[Debug] 正在初始化 PostureDetector...")
    try:
        detector = PostureDetector()
        print("[Debug] 检测器初始化完成")
    except Exception as e:
        print(f"[Error] 检测器初始化崩溃: {e}")
        import traceback
        traceback.print_exc()
        return

    # 打开摄像头
    camera_id = 0
    print(f"[Debug] 正在尝试打开摄像头 ID: {camera_id} ...")
    cap = cv2.VideoCapture(camera_id)
    time.sleep(1.0)

    if not cap.isOpened():
        print(f"[Error] 无法打开摄像头 {camera_id}")
        return
    
    print("[Debug] 摄像头已启动！按 'q' 退出")

    frame_id = 0
    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            while True:
                ret, frame = cap.read()
                if not ret: break

                frame = cv2.flip(frame, 1)
                
                # 检测
                result = detector.process_frame(frame)
                
                # 数据清洗与保存
                save_data = result.copy()
                if "landmarks" in save_data: del save_data["landmarks"]
                
                log_entry = {"frame_id": frame_id, "ts": time.time(), "posture": save_data}
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                f.flush()

                # 显示
                status = "Hunch!" if save_data.get("is_hunchback") else "Normal"
                color = (0, 0, 255) if status == "Hunch!" else (0, 255, 0)
                cv2.putText(frame, f"Posture: {status}", (30, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                cv2.imshow("Posture Check", frame)
                
                frame_id += 1
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except Exception as e:
        print(f"[Runtime Error] {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()