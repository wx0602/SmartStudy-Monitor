import sys
import cv2
import json
import time
import numpy as np
import traceback
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

# 引入配置管理器
from app.config_manager import ConfigManager

# 确保能找到 modules 文件夹
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 尝试导入 AI 模块 (防报错机制)
try:
    from modules.posture.detector import PostureDetector
    from modules.attention.monitor import AttentionMonitor
    from modules.behavior.behavior_detector import BehaviorDetector
except ImportError:
    print("❌ 警告: 找不到 modules 文件夹，AI 功能将不可用")
    PostureDetector = None
    AttentionMonitor = None
    BehaviorDetector = None

# 数据包装类 (用于在不同模块间传递 MediaPipe 结果)
class DetectionResultsWrapper:
    def __init__(self, pose_landmarks, hand_landmarks):
        self.pose_landmarks = pose_landmarks 
        self.multi_hand_landmarks = hand_landmarks

# 辅助函数：将角度标准化到 [-90, 90]
def normalize_angle(angle):
    if angle is None: return 0.0
    while angle > 90: angle -= 180
    while angle < -90: angle += 180
    return round(angle, 2)

# === AI 工作线程 ===
# 功能：在后台运行繁重的 AI 运算，避免卡死界面
class AIWorker(QThread):
    # 信号：将处理好的图片发给界面显示
    change_pixmap_signal = pyqtSignal(np.ndarray)
    # 信号：将 AI 数据字典发给界面更新数值
    update_data_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cam_id = 0 # 默认摄像头 ID
        
        # 初始化配置管理
        self.config_mgr = ConfigManager()
        self.shoulder_thresh = self.config_mgr.get("shoulder_tilt", 10.0)
        self.neck_thresh = self.config_mgr.get("neck_tilt", 15.0)

        # 日志路径设置
        self.log_dir = project_root / "logs"
        self.log_file = self.log_dir / "monitor_data.jsonl"
        self.reset_log_file()

        # 初始化 AI 模型
        self.init_models()

    # 初始化所有 AI 模型
    def init_models(self):
        try:
            # 1. 姿态检测
            self.module_a = PostureDetector() if PostureDetector else None
            
            # 2. 注意力检测 (注入免校准参数)
            self.module_b = AttentionMonitor(fps=30) if AttentionMonitor else None
            if self.module_b:
                self.module_b.calibrator.EAR_BASELINE = 0.25
                self.module_b.calibrator.POSE_BASELINE_READY = True
                self.module_b.calibrator.GAZE_BASELINE_READY = True
            
            # 3. 行为检测 (传入配置)
            self.module_c = BehaviorDetector(self.config_mgr.data) if BehaviorDetector else None

            # 4. MediaPipe 手部模型 (用于行为辅助)
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands.Hands(
                max_num_hands=2, 
                min_detection_confidence=0.5, 
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_pose_conn = mp.solutions.pose.POSE_CONNECTIONS
            
        except Exception as e:
            print(f"❌ 模型初始化失败: {e}")
            traceback.print_exc()

    # 启动时清空旧日志
    def reset_log_file(self):
        try:
            if not self.log_dir.exists():
                self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception: pass

    # 保存日志到文件
    def save_log(self, data_a, data_b, data_c):
        try:
            log_entry = {
                "ts": round(time.time(), 3),
                "posture": {
                    "hunch": bool(data_a.get("is_hunchback")),
                    "lean": bool(data_a.get("is_shoulder_tilted")),
                    "neck": data_a.get("neck_tilt", 0)
                },
                "attention": {
                    "score": int(data_b.get("attention_score", 0)),
                    "fatigue": float(data_b.get("perclos", 0))
                },
                "behavior": {
                    "phone": bool(data_c.get("手机使用", {}).get("使用手机"))
                }
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception: pass

    # 线程主循环
    def run(self):
        cap = cv2.VideoCapture(self.cam_id)
        if not cap.isOpened():
            self.update_data_signal.emit({"Error": "Camera Fail"})
            return
        
        while self._run_flag:
            ret, frame = cap.read()
            if not ret: break
            
            # 镜像翻转并转 RGB
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                # --- A: 坐姿检测 ---
                data_a = {}
                pose_landmarks = None
                if self.module_a:
                    data_a = self.module_a.process_frame(frame)
                    pose_landmarks = data_a.get("landmarks")
                    
                    # 关键修复：标准化角度并重新判断
                    s_ang = normalize_angle(data_a.get("shoulder_tilt_angle"))
                    n_ang = normalize_angle(data_a.get("neck_tilt"))
                    
                    data_a["shoulder_tilt_angle"] = s_ang
                    data_a["neck_tilt"] = n_ang
                    # 使用 ConfigManager 里的阈值进行判断
                    data_a["is_shoulder_tilted"] = abs(s_ang) > self.shoulder_thresh
                    data_a["is_neck_tilted"] = abs(n_ang) > self.neck_thresh

                # --- 手部关键点 ---
                hands_results = self.mp_hands.process(frame_rgb)

                # --- B: 注意力检测 ---
                data_b = {}
                if self.module_b:
                    try:
                        res = self.module_b.process(frame)
                        data_b = json.loads(res) if isinstance(res, str) else res
                    except: pass

                # --- C: 行为检测 ---
                data_c = {}
                if self.module_c:
                    wrapper = DetectionResultsWrapper(pose_landmarks, hands_results.multi_hand_landmarks)
                    data_c = self.module_c.process(wrapper, frame=frame)

                # 写日志 & 发送数据给 UI
                self.save_log(data_a, data_b, data_c)
                self.update_data_signal.emit({"A": data_a, "B": data_b, "C": data_c})

                self.change_pixmap_signal.emit(frame_rgb)
                
            except Exception:
                # 生产环境通常不打印详细错误，防止刷屏
                pass 
            
            # 控制帧率 (约 30fps)
            time.sleep(0.03)

        cap.release()

    # 停止线程
    def stop(self):
        self._run_flag = False
        self.wait()