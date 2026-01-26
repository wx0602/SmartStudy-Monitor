import time
from collections import deque
import numpy as np


class HandBadHabitsDetector:
    def __init__(self, config):
        hand_cfg = config["hand"]

        # 距离阈值
        self.face_threshold = hand_cfg["face_distance"]
        self.head_threshold = hand_cfg["head_distance"]

        # 时间阈值（秒）
        self.touch_duration_threshold = hand_cfg["touch_time_threshold"]
        self.head_duration_threshold = hand_cfg["head_time_threshold"]

        self.smoothing_alpha = hand_cfg.get("smoothing_alpha", 0.4)  
        self.contact_grace = hand_cfg.get("contact_grace", 0.25)   
        self.forehead_offset_y = hand_cfg.get("forehead_offset_y", 0.02) 
        self.mouth_offset_y = hand_cfg.get("mouth_offset_y", 0.0)        
        self.cheek_offset_x = hand_cfg.get("cheek_offset_x", 0.03)       
        self.face_hysteresis_frames = hand_cfg.get("face_hysteresis_frames", 7)  
        self.face_required_ratio = hand_cfg.get("face_required_ratio", 0.6)

        # 状态记录
        self.touch_start_time = None
        self.head_start_time = None
        self.last_face_contact_time = None
        self.last_head_contact_time = None
        self.ema_face_dist = None
        self.ema_head_dist = None
        self.face_touch_window = deque(maxlen=20)

    def _distance(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def _euclid(self, p1, p2):
        return float(np.linalg.norm(np.array(p1) - np.array(p2)))

    def _ema(self, prev, value, alpha):
        if prev is None:
            return value
        return alpha * value + (1 - alpha) * prev

    def _safe_get(self, lm_list, idx):
        try:
            lm = lm_list[idx]
            return (lm.x, lm.y)
        except Exception:
            return None

    def detect_hand_bad_habits(self, results):
        output = {
            "托腮": False,
            "扶额": False,
            "频繁摸脸": False,
            "频繁撑头": False
        }

        if not results.multi_hand_landmarks or not results.pose_landmarks:
            self._reset_state()
            return output

        pose_lm = results.pose_landmarks.landmark
        nose = self._safe_get(pose_lm, 0)
        left_eye = self._safe_get(pose_lm, 2)
        right_eye = self._safe_get(pose_lm, 5)
        mouth_l = self._safe_get(pose_lm, 9)
        mouth_r = self._safe_get(pose_lm, 10)
        left_shoulder = self._safe_get(pose_lm, 11)
        right_shoulder = self._safe_get(pose_lm, 12)

        # 面部/口部中心
        if mouth_l and mouth_r:
            mouth_center = ((mouth_l[0] + mouth_r[0]) / 2.0, (mouth_l[1] + mouth_r[1]) / 2.0 + self.mouth_offset_y)
        elif nose:
            mouth_center = (nose[0], nose[1] + 0.03 + self.mouth_offset_y)
        else:
            if left_shoulder and right_shoulder:
                mouth_center = ((left_shoulder[0] + right_shoulder[0]) / 2.0, (left_shoulder[1] + right_shoulder[1]) / 2.0)
            else:
                mouth_center = (0.5, 0.5)

        # 眼睛中心与额头参考点
        if left_eye and right_eye:
            eye_center = ((left_eye[0] + right_eye[0]) / 2.0, (left_eye[1] + right_eye[1]) / 2.0)
            forehead_center = (eye_center[0], eye_center[1] - self.forehead_offset_y)
        elif nose:
            eye_center = (nose[0], max(0.0, nose[1] - 0.03))
            forehead_center = (eye_center[0], max(0.0, eye_center[1] - self.forehead_offset_y))
        else:
            eye_center = (0.5, 0.45)
            forehead_center = (0.5, 0.43)

        scale_ref = None
        if left_eye and right_eye:
            scale_ref = self._euclid(left_eye, right_eye)
        elif left_shoulder and right_shoulder:
            scale_ref = self._euclid(left_shoulder, right_shoulder)
        else:
            scale_ref = 0.2

        dyn_face_th = max(self.face_threshold, 0.6 * scale_ref)
        dyn_head_th = max(self.head_threshold, 0.7 * scale_ref)

        now = time.time()

        touching_face = False
        touching_head = False

        min_face_dist = float("inf")
        min_head_dist = float("inf")
        min_face_y = None
        min_head_y = None

        for hand in results.multi_hand_landmarks:
            hlm = hand.landmark
           
            pts_idx = [0, 8, 12, 16, 20]
            pts = [self._safe_get(hlm, i) for i in pts_idx]
            mcp_idxs = [5, 9, 13, 17]
            mcp_pts = [self._safe_get(hlm, i) for i in mcp_idxs]
            mcp_pts = [p for p in mcp_pts if p is not None]
            if pts[0] is not None and mcp_pts:
                palm_cx = (pts[0][0] + sum(p[0] for p in mcp_pts)) / (1 + len(mcp_pts))
                palm_cy = (pts[0][1] + sum(p[1] for p in mcp_pts)) / (1 + len(mcp_pts))
                pts.append((palm_cx, palm_cy))
            pts = [p for p in pts if p is not None]

            for p in pts:
                d_face = self._euclid(p, mouth_center)
                if d_face < min_face_dist:
                    min_face_dist = d_face
                    min_face_y = p[1]
                    min_face_x = p[0]
                d_head = self._euclid(p, forehead_center)
                if d_head < min_head_dist:
                    min_head_dist = d_head
                    min_head_y = p[1]

        self.ema_face_dist = self._ema(self.ema_face_dist, min_face_dist, self.smoothing_alpha)
        self.ema_head_dist = self._ema(self.ema_head_dist, min_head_dist, self.smoothing_alpha)

        touching_face = self.ema_face_dist is not None and self.ema_face_dist < dyn_face_th
        touching_head = self.ema_head_dist is not None and self.ema_head_dist < dyn_head_th

        if touching_head and min_head_y is not None:
            touching_head = bool(min_head_y <= eye_center[1])  
        if touching_face and min_face_y is not None:
           
            lateral_ok = True
            if nose is not None:
                lateral_ok = abs((min_face_x if 'min_face_x' in locals() else mouth_center[0]) - nose[0]) >= self.cheek_offset_x
            touching_face = bool((min_face_y >= eye_center[1] - 0.02) and lateral_ok)

        if touching_face is not None:
            self.face_touch_window.append(bool(touching_face))
            k = min(len(self.face_touch_window), self.face_hysteresis_frames)
            recent = list(self.face_touch_window)[-k:]
            if k > 0:
                touching_face = (sum(1 for v in recent if v) / float(k)) >= self.face_required_ratio

        # 摸脸 / 托腮（托腮即时触发，频繁摸脸需持续）
        if touching_face:
            output["托腮"] = True

            if self.touch_start_time is None:
                if self.last_face_contact_time and (now - self.last_face_contact_time) <= self.contact_grace:
                    self.touch_start_time = now - min(self.contact_grace, self.touch_duration_threshold * 0.5)
                else:
                    self.touch_start_time = now
            elif now - self.touch_start_time >= self.touch_duration_threshold:
                output["频繁摸脸"] = True
            self.last_face_contact_time = now
        else:
            self.last_face_contact_time = now if self.last_face_contact_time is None else self.last_face_contact_time
            if self.last_face_contact_time and (now - self.last_face_contact_time) > self.contact_grace:
                self.touch_start_time = None
                self.last_face_contact_time = None

        # 扶额 / 撑头（扶额即时触发，频繁撑头需持续）
        if touching_head:
            output["扶额"] = True

            if self.head_start_time is None:
                if self.last_head_contact_time and (now - self.last_head_contact_time) <= self.contact_grace:
                    self.head_start_time = now - min(self.contact_grace, self.head_duration_threshold * 0.5)
                else:
                    self.head_start_time = now
            elif now - self.head_start_time >= self.head_duration_threshold:
                output["频繁撑头"] = True
            self.last_head_contact_time = now
        else:
            self.last_head_contact_time = now if self.last_head_contact_time is None else self.last_head_contact_time
            if self.last_head_contact_time and (now - self.last_head_contact_time) > self.contact_grace:
                self.head_start_time = None
                self.last_head_contact_time = None

        return output

    def _reset_state(self):
        self.touch_start_time = None
        self.head_start_time = None
        self.last_face_contact_time = None
        self.last_head_contact_time = None
        self.ema_face_dist = None
        self.ema_head_dist = None
        self.face_touch_window.clear()