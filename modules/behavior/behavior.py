import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import json
import yaml
import time
import sys
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 1. 项目根目录定位
THIS_FILE = Path(__file__).resolve()
BASE_DIR = THIS_FILE.parents[2]

if not (BASE_DIR / "config").exists():
    raise RuntimeError(f"无法定位项目根目录: {BASE_DIR}")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. 模块导入
from modules.behavior.behavior_detector import BehaviorDetector

# 3. 配置路径
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
THRESHOLDS_PATH = CONFIG_DIR / "thresholds.yaml"

# 4. 日志路径
OUTPUT_PATH = BASE_DIR / "behavior_results.json"

# 5. MediaPipe 结果封装
class Results:
    def __init__(self, hands_results, pose_results):
        self.multi_hand_landmarks = (
            hands_results.multi_hand_landmarks if hands_results else None
        )
        self.pose_landmarks = pose_results.pose_landmarks if pose_results else None

# 6. 字体
FONT_PATH = BASE_DIR / "assets" / "fonts" / "msyh.ttc"
FONT = ImageFont.truetype(str(FONT_PATH), 18)

# 7. 行为状态显示（左上角）
def draw_behavior_status(frame, behavior_result, origin=(10, 20)):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    x, y = origin
    line_height = 22

    for group, content in behavior_result.items():
        draw.text((x, y), f"{group}:", font=FONT, fill=(0, 0, 0 ))
        y += line_height

        if isinstance(content, dict):
            for k, v in content.items():
                color = (220, 0, 0) if v else (0, 200, 0)
                draw.text((x + 12, y), f"{k}: {v}", font=FONT, fill=color)
                y += line_height
        else:
            color = (220, 0, 0) if content else (0, 200, 0)
            draw.text((x + 12, y), f"{content}", font=FONT, fill=color)
            y += line_height

        y += 6 

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# 8. 画肩部中心
def draw_shoulder_center(frame, results):
    if not results.pose_landmarks:
        return frame

    lm = results.pose_landmarks.landmark
    left_shoulder = lm[11]
    right_shoulder = lm[12]

    h, w, _ = frame.shape
    cx = int((left_shoulder.x + right_shoulder.x) / 2 * w)
    cy = int((left_shoulder.y + right_shoulder.y) / 2 * h)

    cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1)
    cv2.putText(
        frame,
        "Shoulder Center",
        (cx + 8, cy - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (0, 255, 255),
        1,
    )

    return frame

# 9. 主函数
def main():
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        settings = json.load(f)

    with THRESHOLDS_PATH.open("r", encoding="utf-8") as f:
        thresholds = yaml.safe_load(f)

    print_interval = settings.get("output", {}).get("print_interval", 5)

    behavior_detector = BehaviorDetector(thresholds)

    mp_hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    mp_pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera_id = settings.get("camera", {}).get("camera_id", 0)
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise RuntimeError("摄像头打开失败")

    frame_id = 0
    last_log_time = time.time()

    with OUTPUT_PATH.open("w", encoding="utf-8") as log_file:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            pose_results = mp_pose.process(rgb)
            hands_results = mp_hands.process(rgb)

            results = Results(hands_results, pose_results)
            behavior_result = behavior_detector.process(results, frame=frame)

            now = time.time()
            if now - last_log_time >= print_interval:
                log_file.write(
                    json.dumps(
                        {
                            "frame_id": frame_id,
                            "timestamp": now,
                            "behavior": behavior_result,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                last_log_time = now

            frame_id += 1

            frame = draw_shoulder_center(frame, results)
            frame = draw_behavior_status(frame, behavior_result)

            cv2.imshow("Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

# 10. 入口
if __name__ == "__main__":
    main()
