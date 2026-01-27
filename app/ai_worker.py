import sys
import os
import cv2
import json
import time
import traceback
import numpy as np
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal


def resource_path(relative_path):
    """
    获取资源的绝对路径。
    适配开发环境和 PyInstaller 打包后的临时路径 (_MEIPASS)。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_log_dir():
    """
    获取日志存储目录。
    开发环境：项目根目录/logs
    打包环境：可执行文件同级目录/logs
    """
    if hasattr(sys, 'frozen'):
        # 打包后，日志保存在 exe 同级目录下
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境，日志保存在项目根目录下
        base_dir = str(Path(__file__).resolve().parents[2])

    return Path(base_dir) / "logs"


# 配置项目根路径，确保能找到 modules 包
if hasattr(sys, '_MEIPASS'):
    project_root = Path(sys._MEIPASS)
else:
    project_root = Path(__file__).resolve().parents[2]

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


# 尝试导入配置管理器
try:
    from app.config_manager import ConfigManager
except ImportError:
    try:
        sys.path.append(str(Path(__file__).resolve().parents[2]))
        from app.config_manager import ConfigManager
    except Exception:
        print("Warning: ConfigManager import failed, using default config.")
        ConfigManager = None

# 尝试导入 AI 模块
try:
    from modules.posture.detector import PostureDetector
    from modules.attention.monitor import AttentionMonitor
    from modules.behavior.behavior_detector import BehaviorDetector
except ImportError:
    print("Warning: AI modules not found, AI features will be limited.")
    PostureDetector = None
    AttentionMonitor = None
    BehaviorDetector = None


class DetectionResultsWrapper:
    """
    数据包装类，用于在不同模块间传递 MediaPipe 检测结果。
    """

    def __init__(self, pose_landmarks, hand_landmarks):
        self.pose_landmarks = pose_landmarks
        self.multi_hand_landmarks = hand_landmarks


def normalize_angle(angle):
    """
    将角度标准化到 [-90, 90] 范围。
    """
    if angle is None:
        return 0.0
    while angle > 90:
        angle -= 180
    while angle < -90:
        angle += 180
    return round(angle, 2)


class AIWorker(QThread):
    """
    AI 工作线程。
    负责在后台运行视频帧读取和 AI 模型推理，避免阻塞 UI 主线程。
    """
    change_pixmap_signal = pyqtSignal(np.ndarray)
    update_data_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cam_id = 0

        # 初始化配置
        self.config_mgr = ConfigManager() if ConfigManager else None
        if self.config_mgr:
            self.shoulder_thresh = self.config_mgr.get("shoulder_tilt", 10.0)
            self.neck_thresh = self.config_mgr.get("neck_tilt", 15.0)
        else:
            self.shoulder_thresh = 10.0
            self.neck_thresh = 15.0

        # 初始化日志路径
        self.log_dir = get_log_dir()
        self.log_file = self.log_dir / "monitor_data.jsonl"
        self.reset_log_file()

        # 初始化模型
        self.init_models()

    def init_models(self):
        """初始化所有 AI 模型组件。"""
        try:
            # 1. 姿态检测
            self.module_a = PostureDetector() if PostureDetector else None

            # 2. 注意力检测 (注入免校准参数)
            self.module_b = AttentionMonitor(fps=30) if AttentionMonitor else None
            if self.module_b:
                self.module_b.calibrator.EAR_BASELINE = 0.25
                self.module_b.calibrator.POSE_BASELINE_READY = True
                self.module_b.calibrator.GAZE_BASELINE_READY = True

            # 3. 行为检测
            config_data = self.config_mgr.data if self.config_mgr else {}
            self.module_c = BehaviorDetector(config_data) if BehaviorDetector else None

            # 4. MediaPipe 手部模型
            import mediapipe as mp
            try:
                mp_solutions = mp.solutions
            except AttributeError:
                from mediapipe.python import solutions as mp_solutions

            self.mp_hands = mp_solutions.hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp_solutions.drawing_utils
            self.mp_pose_conn = mp_solutions.pose.POSE_CONNECTIONS

            print("Info: AIWorker models initialized successfully.")

        except Exception as e:
            print(f"Error: Model initialization failed: {e}")
            traceback.print_exc()

    def reset_log_file(self):
        """启动时重置日志文件。"""
        try:
            if not self.log_dir.exists():
                self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass

    def save_log(self, data_a, data_b, data_c):
        """将检测数据保存到本地日志文件。"""
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
        except Exception:
            pass

    def run(self):
        """线程主循环。"""
        print("Info: AIWorker thread started, opening camera...")
        cap = cv2.VideoCapture(self.cam_id)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            self.update_data_signal.emit({"Error": "Camera Fail"})
            return

        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read video frame.")
                break

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

                    s_ang = normalize_angle(data_a.get("shoulder_tilt_angle"))
                    n_ang = normalize_angle(data_a.get("neck_tilt"))

                    data_a["shoulder_tilt_angle"] = s_ang
                    data_a["neck_tilt"] = n_ang
                    data_a["is_shoulder_tilted"] = abs(s_ang) > self.shoulder_thresh
                    data_a["is_neck_tilted"] = abs(n_ang) > self.neck_thresh

                # --- 手部关键点 ---
                hands_results = None
                if hasattr(self, 'mp_hands'):
                    hands_results = self.mp_hands.process(frame_rgb)

                # --- B: 注意力检测 ---
                data_b = {}
                if self.module_b:
                    try:
                        res = self.module_b.process(frame)
                        data_b = json.loads(res) if isinstance(res, str) else res
                    except Exception:
                        pass

                # --- C: 行为检测 ---
                data_c = {}
                if self.module_c:
                    hand_landmarks = hands_results.multi_hand_landmarks if hands_results else None
                    wrapper = DetectionResultsWrapper(pose_landmarks, hand_landmarks)
                    data_c = self.module_c.process(wrapper, frame=frame)

                # 写日志 & 发送数据给 UI
                self.save_log(data_a, data_b, data_c)
                self.update_data_signal.emit({"A": data_a, "B": data_b, "C": data_c})

                self.change_pixmap_signal.emit(frame_rgb)

            except Exception as e:
                # 打印一次错误后静默
                if not hasattr(self, "_has_printed_error"):
                    print(f"Error: AI loop exception: {e}")
                    traceback.print_exc()
                    self._has_printed_error = True

            time.sleep(0.03)

        cap.release()
        print("Info: AIWorker thread stopped.")

    def stop(self):
        """停止线程。"""
        self._run_flag = False
        self.wait()