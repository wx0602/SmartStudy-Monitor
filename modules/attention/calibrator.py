import cv2
import numpy as np

from .ear import calc_ear_both
from .geometry import circular_mean_deg
from .config import CALIB_REPROJ_ERR_MAX
from .gaze import calc_gaze_proxy_cv


class BaselineCalibrator:
    def __init__(self, baseline_frames: int = 50):
        self.baseline_frames = int(baseline_frames)

        self.baseline_ears = []
        self.pose_yaws = []
        self.pose_pitches = []

        self.gaze_xs = []
        self.gaze_ys = []

        self.EAR_BASELINE = None
        self.yaw0 = 0.0
        self.pitch0 = 0.0
        self.POSE_BASELINE_READY = False

        self.gx0 = 0.0
        self.gy0 = 0.0
        self.GAZE_BASELINE_READY = False

        self.last_pose_err = None

    def is_calibrated(self) -> bool:
        return (self.EAR_BASELINE is not None) and self.POSE_BASELINE_READY and self.GAZE_BASELINE_READY

    def update(self, frame, face_mesh, pose_estimator) -> bool:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        if not res.multi_face_landmarks:
            return False

        lm = res.multi_face_landmarks[0].landmark

        #EAR baseline
        if self.EAR_BASELINE is None:
            ear = calc_ear_both(lm, w, h)
            if ear > 1e-6:
                self.baseline_ears.append(ear)
                if len(self.baseline_ears) >= self.baseline_frames:
                    self.EAR_BASELINE = float(np.median(self.baseline_ears))

        #Pose baseline
        if not self.POSE_BASELINE_READY:
            pose = pose_estimator.calc_pose_abs(lm, w, h)
            if pose is not None:
                yaw_abs, pitch_abs, err, _ = pose
                self.last_pose_err = float(err)
                if float(err) <= float(CALIB_REPROJ_ERR_MAX):
                    self.pose_yaws.append(yaw_abs)
                    self.pose_pitches.append(pitch_abs)
                    if len(self.pose_yaws) >= self.baseline_frames:
                        self.yaw0 = circular_mean_deg(self.pose_yaws)
                        self.pitch0 = circular_mean_deg(self.pose_pitches)
                        self.POSE_BASELINE_READY = True

        #Gaze baseline
        if not self.GAZE_BASELINE_READY:
            g = calc_gaze_proxy_cv(frame, lm, w, h)
            if g is not None:
                gx, gy, q = g
                # 质量门控
                if q >= 0.15:
                    self.gaze_xs.append(float(gx))
                    self.gaze_ys.append(float(gy))
                    if len(self.gaze_xs) >= self.baseline_frames:
                        self.gx0 = float(np.median(self.gaze_xs))
                        self.gy0 = float(np.median(self.gaze_ys))
                        self.GAZE_BASELINE_READY = True

        return self.is_calibrated()
