import cv2
import numpy as np

from .config import (
    FOCAL_SCALE, MIN_EYE_DIST, REPROJ_ERR_MAX
)
from .geometry import wrap_angle


class PoseEstimator:
    """
    更“不断帧”的姿态估计：
    - 10点固定3D模型（不会出现角度被压小的问题）
    - 先 EPNP 给初值，再 ITERATIVE refine；有 prev 就用 prev 做初值
    - 只用重投影误差做过滤（比 RANSAC 更不容易全军覆没）
    """

    def __init__(self):
        self.prev_rvec = None
        self.prev_tvec = None

        # 稳定的10点（不含嘴角，减少表情干扰）
        self.idxs = [1, 168, 10, 152, 33, 133, 362, 263, 234, 454]

        # 与 idxs 对应的固定 3D 模型点（经验平均脸模型）
        self.model_points = np.array([
            [0.0,    0.0,    0.0],    # 1 nose tip
            [0.0,   22.0,  -18.0],    # 168 nose bridge
            [0.0,   55.0,  -35.0],    # 10 forehead center
            [0.0,  -63.0,  -12.0],    # 152 chin
            [-43.0,  32.0,  -26.0],   # 33 left eye outer
            [-20.0,  32.0,  -26.0],   # 133 left eye inner
            [20.0,   32.0,  -26.0],   # 362 right eye inner
            [43.0,   32.0,  -26.0],   # 263 right eye outer
            [-55.0,   5.0,  -35.0],   # 234 left cheek
            [55.0,    5.0,  -35.0],   # 454 right cheek
        ], dtype=np.float64)

    def calc_pose_abs(self, landmarks, img_w, img_h):
        # 质量门控：脸太远就不算
        pL = np.array([landmarks[33].x * img_w,  landmarks[33].y * img_h], dtype=np.float64)
        pR = np.array([landmarks[263].x * img_w, landmarks[263].y * img_h], dtype=np.float64)
        eye_dist = float(np.linalg.norm(pR - pL))
        if eye_dist < float(MIN_EYE_DIST):
            return None

        # 2D点
        image_points = np.array(
            [(landmarks[i].x * img_w, landmarks[i].y * img_h) for i in self.idxs],
            dtype=np.float64
        )

        # 相机内参
        focal_length = float(img_w) * float(FOCAL_SCALE)
        center = (img_w / 2.0, img_h / 2.0)
        camera_matrix = np.array([
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        # 先给一个初值：有 prev 用 prev；没有就用 EPNP 初始化
        if self.prev_rvec is not None and self.prev_tvec is not None:
            ok, rvec, tvec = cv2.solvePnP(
                self.model_points, image_points, camera_matrix, dist_coeffs,
                rvec=self.prev_rvec, tvec=self.prev_tvec,
                useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE
            )
            if not ok:
                return None
        else:
            ok, rvec, tvec = cv2.solvePnP(
                self.model_points, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_EPNP
            )
            if not ok:
                return None

            ok, rvec, tvec = cv2.solvePnP(
                self.model_points, image_points, camera_matrix, dist_coeffs,
                rvec=rvec, tvec=tvec,
                useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE
            )
            if not ok:
                return None

        # 重投影误差过滤
        proj, _ = cv2.projectPoints(self.model_points, rvec, tvec, camera_matrix, dist_coeffs)
        proj = proj.reshape(-1, 2)
        err = float(np.mean(np.linalg.norm(proj - image_points, axis=1)))
        if err > float(REPROJ_ERR_MAX):
            return None

        self.prev_rvec = rvec
        self.prev_tvec = tvec

        # 欧拉角（用 atan2，避免 pitch 掉到 ±180 分支）
        R, _ = cv2.Rodrigues(rvec)
        yaw = np.degrees(np.arctan2(R[0, 2], R[2, 2]))
        pitch = np.degrees(np.arctan2(-R[1, 2], np.sqrt(R[1, 0] ** 2 + R[1, 1] ** 2)))

        yaw = wrap_angle(float(yaw))
        pitch = wrap_angle(float(pitch))
        return yaw, pitch, err, eye_dist

    def reset(self):
        self.prev_rvec = None
        self.prev_tvec = None
