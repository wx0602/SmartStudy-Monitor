"""
手机检测器
使用 YOLO 手机物体检测 的方式判断是否在玩手机
"""

import time
import math
from collections import deque

_yolo_model = None


def _get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO("yolov8n.pt")
            print("[PhoneDetector] YOLO 模型加载成功")
        except ImportError:
            print("[PhoneDetector] 警告: ultralytics 未安装，手机检测功能将不可用")
            print("[PhoneDetector] 请运行: pip install ultralytics")
            _yolo_model = False
        except Exception as e:
            print(f"[PhoneDetector] YOLO 模型加载失败: {e}")
            _yolo_model = False
    return _yolo_model if _yolo_model else None


class PhoneDetector:
    PHONE_CLASS_ID = 67 

    def __init__(self, config):
        phone_cfg = config.get("phone", {})
        
        self.yolo_confidence = phone_cfg.get("yolo_confidence", 0.4)
        self.detection_interval = phone_cfg.get("detection_interval", 3)
        
        self.confirm_threshold = phone_cfg.get("confirm_threshold", 0.6)
        self.exit_threshold = phone_cfg.get("exit_threshold", 0.2)
        
        self.frame_count = 0
        self.last_phone_detected = False
        
        self.detection_window_size = phone_cfg.get("detection_window_size", 10)
        self.detection_history = deque(maxlen=self.detection_window_size)
        
        self.is_using_phone = False
        
        self.yolo_model = _get_yolo_model()

    def _detect_phone_yolo(self, frame):
        """
        使用 YOLO 检测画面中是否有手机
        """
        if self.yolo_model is None or frame is None:
            return False
        
        try:
            h, w = frame.shape[:2]
            scale = min(320 / w, 320 / h)
            if scale < 1:
                new_w, new_h = int(w * scale), int(h * scale)
                import cv2
                small_frame = cv2.resize(frame, (new_w, new_h))
            else:
                small_frame = frame
            
            results = self.yolo_model(small_frame, verbose=False, conf=self.yolo_confidence)
            
            # 检查是否检测到手机
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        if cls_id == self.PHONE_CLASS_ID:
                            conf = float(box.conf[0])
                            if conf >= self.yolo_confidence:
                                return True
            return False
            
        except Exception as e:
            return False

    def detect(self, results, frame=None):
        """
        检测用户是否在使用手机
        进入状态: 需要滑动窗口内60%以上检测到手机
        退出状态: 需要窗口内80%以上没检测到手机
        """
        output = {"使用手机": False}
        
        self.frame_count += 1

        if self.frame_count % self.detection_interval == 0:
            detected = self._detect_phone_yolo(frame)
            self.detection_history.append(detected)
            self.last_phone_detected = detected
        
        if not self.is_using_phone:
            if len(self.detection_history) >= 3:
                recent_window = list(self.detection_history)[-5:]
                phone_ratio = sum(recent_window) / len(recent_window)
                if phone_ratio >= self.confirm_threshold:
                    self.is_using_phone = True
        
        else:
            if len(self.detection_history) >= 3:
                recent_window = list(self.detection_history)[-5:]
                phone_ratio = sum(recent_window) / len(recent_window)
                
                if phone_ratio < self.exit_threshold:
                    self.is_using_phone = False
        
        output["使用手机"] = self.is_using_phone
        return output
