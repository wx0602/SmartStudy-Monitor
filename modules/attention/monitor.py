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
# 移除外部 Calibrator 依赖，防止死锁
# from .calibrator import BaselineCalibrator 
from .windows import median_deque, std_deque
from .gaze import calc_gaze_proxy_cv

mp_face = mp.solutions.face_mesh

class AttentionMonitor:
    """
    专注度监测器（极速启动版）
    """
    def __init__(self, fps=30, baseline_frames=50): # 保留参数兼容性
        self.fps = fps
        self.frame_time = 1.0 / fps

        # 状态计时器
        self.eye_closed_time = 0.0
        self.yaw_off_time = 0.0
        self.pitch_down_time = 0.0
        self.pitch_up_time = 0.0
        self.noface_time = 0.0
        self.gaze_off_time = 0.0

        # 窗口设置
        self.win_len = max(1, int(WINDOW_TIME * fps))

        # 数据窗口
        self.ear_window = deque(maxlen=self.win_len)
        self.yaw_window = deque(maxlen=self.win_len)
        self.pitch_window = deque(maxlen=self.win_len)
        self.gaze_x_window = deque(maxlen=self.win_len)
        self.gaze_y_window = deque(maxlen=self.win_len)

        # 标志位窗口
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

        # 核心模型
        self.face_mesh = mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose_estimator = PoseEstimator()

        # --- 极速校准变量 ---
        self.is_calibrated = False
        self.calibration_buffer = []
        self.CALIB_FRAMES = 10  # 仅需10帧（约0.3秒）即可完成启动

        # 基准值
        self.EAR_BASELINE = 0.30  # 默认安全值
        self.yaw0 = 0.0
        self.pitch0 = 0.0
        self.gx0 = 0.0
        self.gy0 = 0.0

        self.prev_yaw_rel = 0.0
        self.prev_pitch_rel = 0.0
        self.last_metrics = {}

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

        a = self.score_alpha
        self.score_ema = (1.0 - a) * self.score_ema + a * raw_score

        self.last_metrics = dict(
            perclos=perclos, away_ratio=away_ratio, down_ratio=down_ratio,
            up_ratio=up_ratio, noface_ratio=noface_ratio, gaze_ratio=gaze_ratio,
            unstable=unstb,
        )
        return int(round(self.score_ema))

    def process(self, frame) -> str:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        output = make_base_output(self.score_ema)
        
        # --- 1. 无人脸处理 ---
        if not res.multi_face_landmarks:
            self.finish_closed_run_if_needed()
            self.noface_time += self.frame_time
            
            # 填充状态
            self.noface_flags.append(1 if self.noface_time >= NOFACE_GRACE_SEC else 0)
            self.closed_score_flags.append(0)
            self.away_flags.append(0)
            self.down_flags.append(0)
            self.up_flags.append(0)
            self.gaze_flags.append(0)

            # 重置计时
            self.eye_closed_time = 0.0
            self.yaw_off_time = 0.0
            self.pitch_down_time = 0.0
            self.pitch_up_time = 0.0
            self.gaze_off_time = 0.0
            
            output["blink_state"] = "no_face" # UI会显示检测中
            output["attention_score"] = self.calc_attention_score()
            self._fill_output_metrics(output)
            return json.dumps(output, ensure_ascii=False)

        # --- 2. 有人脸，提取数据 ---
        lm = res.multi_face_landmarks[0].landmark
        self.noface_time = 0.0
        self.noface_flags.append(0)

        # 计算原始数据
        raw_ear = calc_ear_both(lm, w, h)
        pose_data = self.pose_estimator.calc_pose_abs(lm, w, h)
        gaze_data = calc_gaze_proxy_cv(frame, lm, w, h)

        # --- 3. 极速校准逻辑 ---
        if not self.is_calibrated:
            if pose_data is not None:
                # 收集当前帧数据
                yaw, pitch, _, _ = pose_data
                gx, gy = (gaze_data[0], gaze_data[1]) if gaze_data else (0.0, 0.0)
                
                self.calibration_buffer.append({
                    "ear": raw_ear,
                    "yaw": yaw,
                    "pitch": pitch,
                    "gx": gx,
                    "gy": gy
                })

                # 收集满10帧（约0.3秒），计算基准值
                if len(self.calibration_buffer) >= self.CALIB_FRAMES:
                    ears = [d["ear"] for d in self.calibration_buffer]
                    yaws = [d["yaw"] for d in self.calibration_buffer]
                    pitchs = [d["pitch"] for d in self.calibration_buffer]
                    
                    # 策略：EAR取最大值（假设这期间至少睁过一次眼），防止闭眼校准
                    self.EAR_BASELINE = max(max(ears), 0.20) # 兜底0.20
                    # 策略：角度取中位数，过滤抖动
                    self.yaw0 = np.median(yaws)
                    self.pitch0 = np.median(pitchs)
                    self.gx0 = np.median([d["gx"] for d in self.calibration_buffer])
                    self.gy0 = np.median([d["gy"] for d in self.calibration_buffer])
                    
                    self.is_calibrated = True
                    print(f"校准完成: EAR={self.EAR_BASELINE:.2f}, Yaw={self.yaw0:.1f}")

            # 校准期间返回“检测中”
            output["blink_state"] = "no_face" 
            return json.dumps(output, ensure_ascii=False)

        # --- 4. 正常运行逻辑 ---
        
        # 4.1 眼睛状态
        self.ear_window.append(raw_ear)
        # 动态修正：如果发现眼睛睁得比基准还大，慢慢调高基准（适应环境）
        if raw_ear > self.EAR_BASELINE:
             self.EAR_BASELINE = 0.99 * self.EAR_BASELINE + 0.01 * raw_ear

        ear_ratio = raw_ear / max(1e-6, self.EAR_BASELINE)
        output["ear"] = round(float(ear_ratio), 3)

        if ear_ratio < EAR_CLOSED_RATIO:
            blink_state = "closed"
        elif ear_ratio < EAR_HALF_RATIO:
            blink_state = "half"
        else:
            blink_state = "open"
        output["blink_state"] = blink_state

        # 4.2 视线
        if blink_state == "closed" or gaze_data is None:
             self.gaze_flags.append(0)
             self.gaze_off_time = 0.0
             output["gaze_off"] = False
        else:
             gx, gy, q = gaze_data
             if q < 0.15:
                 self.gaze_flags.append(0)
             else:
                 # 减去基准值
                 gx -= self.gx0
                 gy -= self.gy0
                 self.gaze_x_window.append(gx)
                 self.gaze_y_window.append(gy)
                 gx_s = np.median(self.gaze_x_window)
                 gy_s = np.median(self.gaze_y_window)
                 
                 is_off = (abs(gx_s) > GAZE_X_THRESHOLD) or (abs(gy_s) > GAZE_Y_THRESHOLD)
                 self.gaze_flags.append(1 if is_off else 0)
                 if is_off: self.gaze_off_time += self.frame_time
                 else: self.gaze_off_time = 0.0
                 output["gaze_off"] = (self.gaze_off_time >= GAZE_HOLD_TIME)

        # 4.3 头部姿态
        if pose_data is None:
            # 姿态丢失处理
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
        else:
            yaw_abs, pitch_abs, _, _ = pose_data
            
            # 计算相对角度
            yaw_rel = wrap_angle(yaw_abs - self.yaw0)
            pitch_rel = wrap_angle(pitch_abs - self.pitch0)

            # 防抖动平滑
            dy = wrap_angle(yaw_rel - self.prev_yaw_rel)
            if abs(dy) > MAX_POSE_JUMP: 
                yaw_rel = wrap_angle(self.prev_yaw_rel + np.clip(dy, -MAX_POSE_JUMP, MAX_POSE_JUMP))
            self.prev_yaw_rel = yaw_rel
            
            dp = wrap_angle(pitch_rel - self.prev_pitch_rel)
            if abs(dp) > MAX_POSE_JUMP:
                pitch_rel = wrap_angle(self.prev_pitch_rel + np.clip(dp, -MAX_POSE_JUMP, MAX_POSE_JUMP))
            self.prev_pitch_rel = pitch_rel

            # EMA 更新
            a = self.pose_ema_alpha
            self.yaw_ema = (1 - a) * self.yaw_ema + a * yaw_rel
            self.pitch_ema = (1 - a) * self.pitch_ema + a * pitch_rel
            
            self.yaw_window.append(self.yaw_ema)
            self.pitch_window.append(self.pitch_ema)
            
            yaw_s = float(np.median(self.yaw_window))
            pitch_s = float(np.median(self.pitch_window))
            output["yaw_angle"] = round(yaw_s, 2)
            output["pitch_angle"] = round(pitch_s, 2)

            # 闭眼计时
            if blink_state == "closed":
                self.eye_closed_time += self.frame_time
                self.closed_run_frames += 1
                self.closed_score_flags.append(1)
            else:
                self.finish_closed_run_if_needed()
                self.eye_closed_time = 0.0
                self.closed_score_flags.append(0)

            # 偏头判定
            is_away = (abs(yaw_s) > YAW_THRESHOLD)
            self.away_flags.append(1 if is_away else 0)
            if is_away: self.yaw_off_time += self.frame_time
            else: self.yaw_off_time = 0.0

            # 低头判定
            pitch_down = PITCH_DOWN_SIGN * pitch_s
            is_down = (pitch_down > PITCH_DOWN_THRESHOLD)
            self.down_flags.append(1 if is_down else 0)
            if is_down: self.pitch_down_time += self.frame_time
            else: self.pitch_down_time = 0.0
            
            # 抬头判定
            pitch_up = -pitch_down
            is_up = (pitch_up > PITCH_UP_THRESHOLD)
            self.up_flags.append(1 if is_up else 0)
            if is_up: self.pitch_up_time += self.frame_time
            else: self.pitch_up_time = 0.0

        # 计算最终分数
        output["attention_score"] = self.calc_attention_score()
        self._fill_output_metrics(output)
        return json.dumps(output, ensure_ascii=False)

    def _fill_output_metrics(self, output):
        m = self.last_metrics
        output["perclos"] = round(m.get("perclos", 0.0), 3)
        output["away_ratio"] = round(m.get("away_ratio", 0.0), 3)
        output["down_ratio"] = round(m.get("down_ratio", 0.0), 3)
        output["up_ratio"] = round(m.get("up_ratio", 0.0), 3)
        output["noface_ratio"] = round(m.get("noface_ratio", 0.0), 3)
        output["gaze_ratio"] = round(m.get("gaze_ratio", 0.0), 3)
        output["unstable"] = round(m.get("unstable", 0.0), 3)