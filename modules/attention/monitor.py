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
    """
    专注度监测器
    """
    def __init__(self, fps=30, baseline_frames=50):
        """
        初始化监测器。

        Args:
            fps (int): 视频流帧率
            baseline_frames (int): 校准阶段所需的帧数
        """
        self.fps = fps
        self.frame_time = 1.0 / fps

        # 各类违规状态持续时间（秒）
        self.eye_closed_time = 0.0
        self.yaw_off_time = 0.0
        self.pitch_down_time = 0.0
        self.pitch_up_time = 0.0

        self.noface_time = 0.0
        self.gaze_off_time = 0.0

        # 根据配置的时间窗口计算对应的帧数长度
        self.win_len = max(1, int(WINDOW_TIME * fps))

        # 数值滑动窗口
        self.ear_window = deque(maxlen=self.win_len)
        self.yaw_window = deque(maxlen=self.win_len)
        self.pitch_window = deque(maxlen=self.win_len)
        self.gaze_x_window = deque(maxlen=self.win_len)
        self.gaze_y_window = deque(maxlen=self.win_len)

        # 状态标志滑动窗口 (存储 0 或 1)
        self.closed_score_flags = deque(maxlen=self.win_len)
        self.away_flags = deque(maxlen=self.win_len)
        self.down_flags = deque(maxlen=self.win_len)
        self.up_flags = deque(maxlen=self.win_len)
        self.noface_flags = deque(maxlen=self.win_len)
        self.gaze_flags = deque(maxlen=self.win_len)

        # 连续闭眼帧计数，用于过滤瞬时眨眼
        self.closed_run_frames = 0

        # 分数计算相关的 EMA 参数
        self.score_ema = 100.0
        self.score_alpha = SCORE_EMA_ALPHA

        # 姿态角度的 EMA 参数
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

        # 用于处理角度跳变（防万向节锁或周期跳变）
        self.prev_yaw_rel = 0.0
        self.prev_pitch_rel = 0.0

        # 缓存上一帧的计算指标
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
        """
        如果闭眼片段时长短于阈值（如正常眨眼），则回溯修正标志位。
        防止因正常眨眼导致专注度分数下降。
        """
        if self.closed_run_frames <= 0:
            return

        dur = self.closed_run_frames * self.frame_time
        if dur < BLINK_MIN_SEC:
            # 回溯清除窗口中的闭眼标记
            k = min(self.closed_run_frames, len(self.closed_score_flags))
            for i in range(k):
                idx = len(self.closed_score_flags) - 1 - i
                if idx >= 0:
                    self.closed_score_flags[idx] = 0

        self.closed_run_frames = 0

    def calibrate(self, frame):
        return self.calibrator.update(frame, self.face_mesh, self.pose_estimator)

    def calc_attention_score(self):
        """
        计算当前的专注度分数 (0-100)。
        逻辑基于滑动窗口内的各类违规比例和头部运动稳定性。
        """
        n = len(self.closed_score_flags)
        if n <= 0:
            self.last_metrics = {}
            return int(round(self.score_ema))

        # 计算各类违规行为在窗口期内的占比
        perclos = float(sum(self.closed_score_flags)) / n
        away_ratio = float(sum(self.away_flags)) / n
        down_ratio = float(sum(self.down_flags)) / n
        up_ratio = float(sum(self.up_flags)) / n
        noface_ratio = float(sum(self.noface_flags)) / n
        gaze_ratio = float(sum(self.gaze_flags)) / n

        # 计算头部稳定性（标准差）
        yaw_std = std_deque(self.yaw_window) if len(self.yaw_window) > 5 else 0.0
        pitch_std = std_deque(self.pitch_window) if len(self.pitch_window) > 5 else 0.0

        # 归一化稳定性分数
        unstb = 0.5 * min(1.0, yaw_std / max(1e-6, YAW_STD_NORM)) + \
                0.5 * min(1.0, pitch_std / max(1e-6, PITCH_STD_NORM))
        unstb = float(min(1.0, max(0.0, unstb)))

        # 计算加权扣分
        penalty = 0.0
        penalty += W_EYE * perclos * 100.0
        penalty += W_AWAY * away_ratio * 100.0
        penalty += W_DOWN * down_ratio * 100.0
        penalty += W_UP * up_ratio * 100.0
        penalty += W_NOFACE * noface_ratio * 100.0
        penalty += W_GAZE * gaze_ratio * 100.0
        penalty += W_UNSTB * unstb * 100.0

        raw_score = 100.0 - penalty
        raw_score = max(0.0, min(100.0, raw_score))

        # 使用 EMA 进行平滑处理
        a = self.score_alpha
        self.score_ema = (1.0 - a) * self.score_ema + a * raw_score

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
        """
        处理单帧图像，返回 JSON 格式的监测结果。
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        output = make_base_output(self.score_ema)

        # 未检测到人脸或未完成校准的情况
        if (not res.multi_face_landmarks) or (not self.is_calibrated()):
            self.finish_closed_run_if_needed()

            if not res.multi_face_landmarks:
                self.noface_time += self.frame_time
            else:
                self.noface_time = 0.0

            # 填充状态标志位
            self.noface_flags.append(1 if self.noface_time >= NOFACE_GRACE_SEC else 0)
            self.closed_score_flags.append(0)
            self.away_flags.append(0)
            self.down_flags.append(0)
            self.up_flags.append(0)
            self.gaze_flags.append(0)

            # 重置计时器
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

        # 检测到人脸的情况
        lm = res.multi_face_landmarks[0].landmark
        self.noface_time = 0.0
        self.noface_flags.append(0)

        # 计算 EAR
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

        # 计算视线 (Gaze)
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

                if q < 0.15:
                    self.gaze_flags.append(0)
                    self.gaze_off_time = 0.0
                    output["gaze_x"] = None
                    output["gaze_y"] = None
                    output["gaze_off"] = False
                else:
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

        # 计算头部姿态 (Pose)
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

        # 计算相对角度并处理跳变
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

        # 平滑更新
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
        """
        重置运行时状态，用于校准完成后清空历史数据。
        """
        self.eye_closed_time = 0.0
        self.yaw_off_time = 0.0
        self.pitch_down_time = 0.0
        self.pitch_up_time = 0.0
        self.noface_time = 0.0
        self.gaze_off_time = 0.0

        self.closed_run_frames = 0
        self.closed_score_flags.clear()
        self.away_flags.clear()
        self.down_flags.clear()
        self.up_flags.clear()
        self.noface_flags.clear()
        self.gaze_flags.clear()

        self.ear_window.clear()
        self.yaw_window.clear()
        self.pitch_window.clear()
        self.gaze_x_window.clear()
        self.gaze_y_window.clear()

        self.prev_yaw_rel = 0.0
        self.prev_pitch_rel = 0.0

        if hasattr(self, "yaw_ema"):
            self.yaw_ema = 0.0
        if hasattr(self, "pitch_ema"):
            self.pitch_ema = 0.0

        if hasattr(self.pose_estimator, "reset"):
            self.pose_estimator.reset()

        if hasattr(self, "last_metrics"):
            self.last_metrics = {}

        if seed_zero:
            seed_count = max(3, self.win_len // 2)
            for _ in range(seed_count):
                self.yaw_window.append(0.0)
                self.pitch_window.append(0.0)
                self.gaze_x_window.append(0.0)
                self.gaze_y_window.append(0.0)