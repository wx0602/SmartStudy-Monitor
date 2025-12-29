import cv2
import json
import numpy as np
from collections import deque

import mediapipe as mp

from .config import (
    SLEEPY_TIME, YAW_THRESHOLD,
    PITCH_DOWN_THRESHOLD, PITCH_UP_THRESHOLD,
    WINDOW_TIME, POSE_HOLD_TIME,
    EAR_CLOSED_RATIO, EAR_HALF_RATIO,
    PITCH_DOWN_SIGN,
    MAX_POSE_JUMP,
    W_EYE, W_AWAY, W_DOWN, W_UP, W_NOFACE, W_UNSTB,
    YAW_STD_NORM, PITCH_STD_NORM,
    SCORE_EMA_ALPHA, BLINK_MIN_SEC,
    NOFACE_GRACE_SEC,
    GAZE_X_THRESHOLD, GAZE_Y_THRESHOLD, GAZE_HOLD_TIME, W_GAZE,
)
from .geometry import wrap_angle
from .schema import make_base_output
from .ear import calc_ear_both
from .pose import PoseEstimator
from .calibrator import BaselineCalibrator
from .windows import median_deque, std_deque
from .gaze import calc_gaze_proxy_cv

mp_face = mp.solutions.face_mesh


class AttentionMonitor:
    def __init__(self, fps=30, baseline_frames=50):
        self.fps = fps
        self.frame_time = 1.0 / fps

        self.eye_closed_time = 0.0
        self.yaw_off_time = 0.0
        self.pitch_down_time = 0.0
        self.pitch_up_time = 0.0

        self.noface_time = 0.0
        self.gaze_off_time = 0.0

        self.win_len = max(1, int(WINDOW_TIME * fps))

        self.ear_window = deque(maxlen=self.win_len)
        self.yaw_window = deque(maxlen=self.win_len)
        self.pitch_window = deque(maxlen=self.win_len)

        self.gaze_x_window = deque(maxlen=self.win_len)
        self.gaze_y_window = deque(maxlen=self.win_len)

        self.closed_score_flags = deque(maxlen=self.win_len)
        self.away_flags = deque(maxlen=self.win_len)
        self.down_flags = deque(maxlen=self.win_len)
        self.up_flags = deque(maxlen=self.win_len)
        self.noface_flags = deque(maxlen=self.win_len)
        self.gaze_flags = deque(maxlen=self.win_len)

        self.closed_run_frames = 0

        self.score_ema = 100.0
        self.score_alpha = SCORE_EMA_ALPHA

        self.yaw_ema = 0.0
        self.pitch_ema = 0.0
        self.pose_ema_alpha = 0.2

        self.face_mesh = mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.pose_estimator = PoseEstimator()
        self.calibrator = BaselineCalibrator(baseline_frames=baseline_frames)

        self.prev_yaw_rel = 0.0
        self.prev_pitch_rel = 0.0

        self.last_metrics = {}

    def is_calibrated(self):
        return self.calibrator.is_calibrated()

    @property
    def EAR_BASELINE(self):
        return self.calibrator.EAR_BASELINE

    @property
    def yaw0(self):
        return self.calibrator.yaw0

    @property
    def pitch0(self):
        return self.calibrator.pitch0

    @property
    def gx0(self):
        return getattr(self.calibrator, "gx0", 0.0)

    @property
    def gy0(self):
        return getattr(self.calibrator, "gy0", 0.0)

    def finish_closed_run_if_needed(self):
        if self.closed_run_frames <= 0:
            return
        dur = self.closed_run_frames * self.frame_time
        if dur < BLINK_MIN_SEC:
            k = min(self.closed_run_frames, len(self.closed_score_flags))
            for i in range(k):
                idx = len(self.closed_score_flags) - 1 - i
                if idx >= 0:
                    self.closed_score_flags[idx] = 0
        self.closed_run_frames = 0

    def calibrate(self, frame):
        return self.calibrator.update(frame, self.face_mesh, self.pose_estimator)

    def calc_attention_score(self):
        n = len(self.closed_score_flags)
        if n <= 0:
            self.last_metrics = {}
            return int(round(self.score_ema))

        perclos = float(sum(self.closed_score_flags)) / n
        away_ratio = float(sum(self.away_flags)) / n
        down_ratio = float(sum(self.down_flags)) / n
        up_ratio = float(sum(self.up_flags)) / n
        noface_ratio = float(sum(self.noface_flags)) / n
        gaze_ratio = float(sum(self.gaze_flags)) / n

        yaw_std = std_deque(self.yaw_window) if len(self.yaw_window) > 5 else 0.0
        pitch_std = std_deque(self.pitch_window) if len(self.pitch_window) > 5 else 0.0

        unstb = 0.5 * min(1.0, yaw_std / max(1e-6, YAW_STD_NORM)) + \
                0.5 * min(1.0, pitch_std / max(1e-6, PITCH_STD_NORM))
        unstb = float(min(1.0, max(0.0, unstb)))

        raw = 100.0 \
              - W_EYE    * perclos      * 100.0 \
              - W_AWAY   * away_ratio   * 100.0 \
              - W_DOWN   * down_ratio   * 100.0 \
              - W_UP     * up_ratio     * 100.0 \
              - W_NOFACE * noface_ratio * 100.0 \
              - W_GAZE   * gaze_ratio   * 100.0 \
              - W_UNSTB  * unstb        * 100.0

        raw = max(0.0, min(100.0, raw))

        a = self.score_alpha
        self.score_ema = (1.0 - a) * self.score_ema + a * raw

        self.last_metrics = dict(
            perclos=perclos,
            away_ratio=away_ratio,
            down_ratio=down_ratio,
            up_ratio=up_ratio,
            noface_ratio=noface_ratio,
            gaze_ratio=gaze_ratio,
            unstable=unstb,
        )

        return int(round(self.score_ema))

    def process(self, frame) -> str:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        output = make_base_output(self.score_ema)

        if (not res.multi_face_landmarks) or (not self.is_calibrated()):
            self.finish_closed_run_if_needed()

            if not res.multi_face_landmarks:
                self.noface_time += self.frame_time
            else:
                self.noface_time = 0.0

            self.noface_flags.append(1 if self.noface_time >= NOFACE_GRACE_SEC else 0)
            self.closed_score_flags.append(0)
            self.away_flags.append(0)
            self.down_flags.append(0)
            self.up_flags.append(0)
            self.gaze_flags.append(0)

            self.eye_closed_time = 0.0
            self.yaw_off_time = 0.0
            self.pitch_down_time = 0.0
            self.pitch_up_time = 0.0
            self.gaze_off_time = 0.0

            output["attention_score"] = self.calc_attention_score()
            m = self.last_metrics or {}
            output["perclos"] = round(m.get("perclos", 0.0), 3) if m else None
            output["away_ratio"] = round(m.get("away_ratio", 0.0), 3) if m else None
            output["down_ratio"] = round(m.get("down_ratio", 0.0), 3) if m else None
            output["up_ratio"] = round(m.get("up_ratio", 0.0), 3) if m else None
            output["noface_ratio"] = round(m.get("noface_ratio", 0.0), 3) if m else None
            output["gaze_ratio"] = round(m.get("gaze_ratio", 0.0), 3) if m else None
            output["unstable"] = round(m.get("unstable", 0.0), 3) if m else None
            return json.dumps(output, ensure_ascii=False)

        lm = res.multi_face_landmarks[0].landmark
        self.noface_time = 0.0
        self.noface_flags.append(0)

        # ===== EAR =====
        EAR = calc_ear_both(lm, w, h)
        self.ear_window.append(EAR)
        ear_ratio = EAR / max(1e-6, self.EAR_BASELINE)
        output["ear"] = round(float(ear_ratio), 3)

        if ear_ratio < EAR_CLOSED_RATIO:
            blink_state = "closed"
        elif ear_ratio < EAR_HALF_RATIO:
            blink_state = "half"
        else:
            blink_state = "open"
        output["blink_state"] = blink_state

        # ===== GAZE (CV)：闭眼禁用 + 基线校准 + 质量门控 =====
        if blink_state == "closed":
            self.gaze_flags.append(0)
            self.gaze_off_time = 0.0
            output["gaze_x"] = None
            output["gaze_y"] = None
            output["gaze_off"] = False
        else:
            g = calc_gaze_proxy_cv(frame, lm, w, h)
            if g is None:
                self.gaze_flags.append(0)
                self.gaze_off_time = 0.0
                output["gaze_x"] = None
                output["gaze_y"] = None
                output["gaze_off"] = False
            else:
                gx, gy, q = g

                # 质量太差就当不可用（反光/模糊/遮挡）
                if q < 0.15:
                    self.gaze_flags.append(0)
                    self.gaze_off_time = 0.0
                    output["gaze_x"] = None
                    output["gaze_y"] = None
                    output["gaze_off"] = False
                else:
                    # 个人基线：正视不一定为0
                    gx = float(gx - float(self.gx0))
                    gy = float(gy - float(self.gy0))

                    self.gaze_x_window.append(gx)
                    self.gaze_y_window.append(gy)

                    gx_s = float(np.median(self.gaze_x_window))
                    gy_s = float(np.median(self.gaze_y_window))

                    output["gaze_x"] = round(gx_s, 3)
                    output["gaze_y"] = round(gy_s, 3)

                    is_gaze_off = (abs(gx_s) > GAZE_X_THRESHOLD) or (abs(gy_s) > GAZE_Y_THRESHOLD)
                    self.gaze_flags.append(1 if is_gaze_off else 0)
                    self.gaze_off_time = (self.gaze_off_time + self.frame_time) if is_gaze_off else 0.0
                    output["gaze_off"] = (self.gaze_off_time >= GAZE_HOLD_TIME)

        # ===== Pose =====
        pose = self.pose_estimator.calc_pose_abs(lm, w, h)
        if pose is None:
            if blink_state == "closed":
                self.eye_closed_time += self.frame_time
                self.closed_run_frames += 1
                self.closed_score_flags.append(1)
            else:
                self.finish_closed_run_if_needed()
                self.eye_closed_time = 0.0
                self.closed_score_flags.append(0)

            self.away_flags.append(0)
            self.down_flags.append(0)
            self.up_flags.append(0)

            output["yaw_angle"] = round(median_deque(self.yaw_window), 2) if len(self.yaw_window) else None
            output["pitch_angle"] = round(median_deque(self.pitch_window), 2) if len(self.pitch_window) else None

            output["attention_score"] = self.calc_attention_score()
            m = self.last_metrics or {}
            output["perclos"] = round(m.get("perclos", 0.0), 3) if m else None
            output["away_ratio"] = round(m.get("away_ratio", 0.0), 3) if m else None
            output["down_ratio"] = round(m.get("down_ratio", 0.0), 3) if m else None
            output["up_ratio"] = round(m.get("up_ratio", 0.0), 3) if m else None
            output["noface_ratio"] = round(m.get("noface_ratio", 0.0), 3) if m else None
            output["gaze_ratio"] = round(m.get("gaze_ratio", 0.0), 3) if m else None
            output["unstable"] = round(m.get("unstable", 0.0), 3) if m else None
            return json.dumps(output, ensure_ascii=False)

        yaw_abs, pitch_abs, _, _ = pose

        yaw_rel = wrap_angle(yaw_abs - self.yaw0)
        pitch_rel = wrap_angle(pitch_abs - self.pitch0)

        dy = wrap_angle(yaw_rel - self.prev_yaw_rel)
        if abs(dy) > MAX_POSE_JUMP:
            yaw_rel = wrap_angle(self.prev_yaw_rel + float(np.clip(dy, -MAX_POSE_JUMP, MAX_POSE_JUMP)))

        dp = wrap_angle(pitch_rel - self.prev_pitch_rel)
        if abs(dp) > MAX_POSE_JUMP:
            pitch_rel = wrap_angle(self.prev_pitch_rel + float(np.clip(dp, -MAX_POSE_JUMP, MAX_POSE_JUMP)))

        self.prev_yaw_rel = yaw_rel
        self.prev_pitch_rel = pitch_rel

        a = self.pose_ema_alpha
        self.yaw_ema = (1 - a) * self.yaw_ema + a * yaw_rel
        self.pitch_ema = (1 - a) * self.pitch_ema + a * pitch_rel

        self.yaw_window.append(self.yaw_ema)
        self.pitch_window.append(self.pitch_ema)

        yaw_s = float(np.median(self.yaw_window))
        pitch_s = float(np.median(self.pitch_window))

        output["yaw_angle"] = round(yaw_s, 2)
        output["pitch_angle"] = round(pitch_s, 2)

        if blink_state == "closed":
            self.eye_closed_time += self.frame_time
            self.closed_run_frames += 1
            self.closed_score_flags.append(1)
        else:
            self.finish_closed_run_if_needed()
            self.eye_closed_time = 0.0
            self.closed_score_flags.append(0)

        is_away = (abs(yaw_s) > YAW_THRESHOLD)
        self.away_flags.append(1 if is_away else 0)
        self.yaw_off_time = (self.yaw_off_time + self.frame_time) if is_away else 0.0

        pitch_down = PITCH_DOWN_SIGN * pitch_s
        pitch_up = -pitch_down

        is_down = (pitch_down > PITCH_DOWN_THRESHOLD)
        is_up = (pitch_up > PITCH_UP_THRESHOLD)

        self.down_flags.append(1 if is_down else 0)
        self.up_flags.append(1 if is_up else 0)

        self.pitch_down_time = (self.pitch_down_time + self.frame_time) if is_down else 0.0
        self.pitch_up_time = (self.pitch_up_time + self.frame_time) if is_up else 0.0

        output["attention_score"] = self.calc_attention_score()
        m = self.last_metrics or {}
        output["perclos"] = round(m.get("perclos", 0.0), 3) if m else None
        output["away_ratio"] = round(m.get("away_ratio", 0.0), 3) if m else None
        output["down_ratio"] = round(m.get("down_ratio", 0.0), 3) if m else None
        output["up_ratio"] = round(m.get("up_ratio", 0.0), 3) if m else None
        output["noface_ratio"] = round(m.get("noface_ratio", 0.0), 3) if m else None
        output["gaze_ratio"] = round(m.get("gaze_ratio", 0.0), 3) if m else None
        output["unstable"] = round(m.get("unstable", 0.0), 3) if m else None

        return json.dumps(output, ensure_ascii=False)

    def reset_runtime_state(self, seed_zero=True):
        """校准完成后：清空窗口/计时器，让 UI 立刻从 0 开始显示。"""
        # 计时器清零
        self.eye_closed_time = 0.0
        self.yaw_off_time = 0.0
        self.pitch_down_time = 0.0
        self.pitch_up_time = 0.0
        self.noface_time = 0.0
        self.gaze_off_time = 0.0

        # flags & 眨眼段
        self.closed_run_frames = 0
        self.closed_score_flags.clear()
        self.away_flags.clear()
        self.down_flags.clear()
        self.up_flags.clear()
        self.noface_flags.clear()
        self.gaze_flags.clear()

        # 数值窗口清空
        self.ear_window.clear()
        self.yaw_window.clear()
        self.pitch_window.clear()
        self.gaze_x_window.clear()
        self.gaze_y_window.clear()

        # 防爆点状态归零
        self.prev_yaw_rel = 0.0
        self.prev_pitch_rel = 0.0

        # EMA 初值归零
        if hasattr(self, "yaw_ema"):
            self.yaw_ema = 0.0
        if hasattr(self, "pitch_ema"):
            self.pitch_ema = 0.0

        # PoseEstimator 的历史初值清掉
        if hasattr(self.pose_estimator, "reset"):
            self.pose_estimator.reset()

        # 指标缓存
        if hasattr(self, "last_metrics"):
            self.last_metrics = {}

        # 让 UI 第一帧必为 0（中位数=0）
        if seed_zero:
            seed_count = max(3, self.win_len // 2)
            for _ in range(seed_count):
                self.yaw_window.append(0.0)
                self.pitch_window.append(0.0)
                self.gaze_x_window.append(0.0)
                self.gaze_y_window.append(0.0)