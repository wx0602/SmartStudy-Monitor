import numpy as np

# MediaPipe FaceMesh 眼睛关键点
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def calc_ear(landmarks, eye_idx, img_w, img_h) -> float:
    pts = np.array(
        [(landmarks[i].x * img_w, landmarks[i].y * img_h) for i in eye_idx],
        dtype=np.float32
    )
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    if C < 1e-6:
        return 0.0
    return float((A + B) / (2.0 * C))

def calc_ear_both(landmarks, img_w, img_h) -> float:
    left = calc_ear(landmarks, LEFT_EYE, img_w, img_h)
    right = calc_ear(landmarks, RIGHT_EYE, img_w, img_h)
    return float((left + right) / 2.0)
