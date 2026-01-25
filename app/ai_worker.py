import sys
import cv2
import json
import yaml
import time
import os
import numpy as np
import traceback
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

# 确保能找到 modules
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 导入功能模块
try:
    from modules.posture.detector import PostureDetector
    from modules.attention.monitor import AttentionMonitor
    from modules.behavior.behavior_detector import BehaviorDetector
except ImportError:
    PostureDetector = None
    AttentionMonitor = None
    BehaviorDetector = None

class DetectionResultsWrapper:
    def __init__(self, pose_landmarks, hand_landmarks):
        self.pose_landmarks = pose_landmarks 
        self.multi_hand_landmarks = hand_landmarks

def normalize_angle(angle):
    if angle is None: return 0.0
    if angle > 90: angle -= 180
    elif angle < -90: angle += 180
    return round(angle, 2)

class AIWorker(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    update_data_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cam_id = 0
        
        # === 1. 日志文件路径设置 ===
        self.log_dir = project_root / "logs"
        self.log_file = self.log_dir / "monitor_data.jsonl"
        
        # === 2. 启动时自动清空日志 ===
        self.reset_log_file()

        try:
            self.module_a = PostureDetector() if PostureDetector else None
            
            # 暴力破解 AttentionMonitor (免校准)
            self.module_b = AttentionMonitor(fps=30) if AttentionMonitor else None
            if self.module_b:
                self.module_b.calibrator.EAR_BASELINE = 0.25
                self.module_b.calibrator.yaw0 = 0.0
                self.module_b.calibrator.pitch0 = 0.0
                self.module_b.calibrator.gx0 = 0.0
                self.module_b.calibrator.gy0 = 0.0
                self.module_b.calibrator.POSE_BASELINE_READY = True
                self.module_b.calibrator.GAZE_BASELINE_READY = True

            thresholds = {}
            try:
                cfg_path = project_root / "config" / "thresholds.yaml"
                if cfg_path.exists():
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        thresholds = yaml.safe_load(f)
            except: pass
            
            self.module_c = BehaviorDetector(thresholds) if BehaviorDetector else None

            import mediapipe as mp
            self.mp_hands = mp.solutions.hands.Hands(
                max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_pose_conn = mp.solutions.pose.POSE_CONNECTIONS
            
        except Exception as e:
            print(f"❌ 模型初始化失败: {e}")
            traceback.print_exc()

    def reset_log_file(self):
        """清空或创建日志文件"""
        try:
            # 如果 logs 文件夹不存在，创建一个
            if not self.log_dir.exists():
                self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # 以 'w' 模式打开文件会直接清空内容
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("") # 写入空字符串，相当于清空
            print(f"✅ 日志已清空: {self.log_file}")
        except Exception as e:
            print(f"⚠️ 无法重置日志文件: {e}")

    def save_log(self, data_a, data_b, data_c):
        """将当前帧的数据追加写入文件"""
        try:
            # 整理要保存的数据（剔除太大的对象，只留数值）
            log_entry = {
                "timestamp": time.time(),
                "posture": {
                    "hunchback": data_a.get("is_hunchback", False),
                    "shoulder_angle": data_a.get("shoulder_tilt_angle", 0),
                    "neck_angle": data_a.get("neck_tilt", 0)
                },
                "attention": {
                    "score": data_b.get("attention_score", 0),
                    "fatigue": data_b.get("perclos", 0),
                    "yaw": data_b.get("yaw_angle", 0)
                },
                "behavior": {
                    "phone": data_c.get("手机使用", {}).get("使用手机", False),
                    "hands": list(data_c.get("手部行为", {}).keys()) # 只记录动作名称
                }
            }
            
            # 以 'a' (append) 模式追加写入
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception:
            pass # 写日志出错不要卡死主程序

    def run(self):
        cap = cv2.VideoCapture(self.cam_id)
        if not cap.isOpened():
            self.update_data_signal.emit({"Error": "Camera Fail"})
            return
        
        while self._run_flag:
            ret, frame = cap.read()
            if not ret: break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                # --- A: 坐姿 ---
                data_a = {}
                pose_landmarks = None
                if self.module_a:
                    data_a = self.module_a.process_frame(frame)
                    pose_landmarks = data_a.get("landmarks")
                    if "shoulder_tilt_angle" in data_a:
                        data_a["shoulder_tilt_angle"] = normalize_angle(data_a["shoulder_tilt_angle"])
                    if "neck_tilt" in data_a:
                        data_a["neck_tilt"] = normalize_angle(data_a["neck_tilt"])

                # --- Hands ---
                hands_results = self.mp_hands.process(frame_rgb)

                # --- B: 注意力 ---
                data_b = {}
                if self.module_b:
                    try:
                        res = self.module_b.process(frame)
                        data_b = json.loads(res) if isinstance(res, str) else res
                    except: pass

                # --- C: 行为 ---
                data_c = {}
                if self.module_c:
                    wrapper = DetectionResultsWrapper(pose_landmarks, hands_results.multi_hand_landmarks)
                    data_c = self.module_c.process(wrapper, frame=frame)

                # 🔥 保存日志
                self.save_log(data_a, data_b, data_c)

                # 发送 UI 数据
                self.update_data_signal.emit({"A": data_a, "B": data_b, "C": data_c})

                # --- 画面绘制 ---
                if pose_landmarks:
                    self.mp_drawing.draw_landmarks(frame_rgb, pose_landmarks, self.mp_pose_conn)
                
                if data_a.get("is_hunchback"):
                    cv2.putText(frame_rgb, "BAD POSTURE!", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
                
                if data_c and data_c.get("手机使用", {}).get("使用手机"):
                    cv2.putText(frame_rgb, "PHONE DETECTED!", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 165, 0), 3)

                self.change_pixmap_signal.emit(frame_rgb)
                
            except Exception:
                pass 
            
            time.sleep(0.03)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()