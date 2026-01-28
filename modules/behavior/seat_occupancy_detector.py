import numpy as np
import time
import cv2

class SeatOccupancyDetector:
    """
    上半身视角离席检测:
      肩部中心偏移
      Pose 丢失
      时间防抖
    """

    def __init__(self, config):
        seat_cfg = config["seat"]

        self.offset_threshold = seat_cfg.get("offset_threshold", 0.4)
        self.miss_frame_threshold = seat_cfg.get("miss_frame_threshold", 5)

        self.origin_center = None
        self.miss_count = 0

    def _distance(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def detect(self, results):
        output = {
            "离席": False
        }

        if not results.pose_landmarks:
            output["离席"] = True
            return output

        self.miss_count = 0
        self.leave_start_time = None

        lm = results.pose_landmarks.landmark
        left_shoulder = lm[11]
        right_shoulder = lm[12]

        shoulder_center = (
            (left_shoulder.x + right_shoulder.x) / 2,
            (left_shoulder.y + right_shoulder.y) / 2
        )

        if self.origin_center is None:
            if not hasattr(self, "_init_positions"):
                self._init_positions = []
            self._init_positions.append(shoulder_center)
            if len(self._init_positions) >= 10:  # 取前10帧平均
                avg_x = np.mean([p[0] for p in self._init_positions])
                avg_y = np.mean([p[1] for p in self._init_positions])
                self.origin_center = (avg_x, avg_y)
            return output

        offset = self._distance(shoulder_center, self.origin_center)

        if offset > self.offset_threshold:
            output["离席"] = True

        return output

def draw_shoulder_center(self, frame, results):
        """
        绘制肩部中心
        """
        lm = results.pose_landmarks.landmark
        left_shoulder = lm[11]
        right_shoulder = lm[12]

        shoulder_center = (
            (left_shoulder.x + right_shoulder.x) / 2,
            (left_shoulder.y + right_shoulder.y) / 2
        )

        height, width, _ = frame.shape
        x = int(shoulder_center[0] * width)
        y = int(shoulder_center[1] * height)

        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(frame, "Shoulder Center", (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return frame
