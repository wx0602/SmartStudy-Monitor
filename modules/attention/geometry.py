import numpy as np

def wrap_angle(deg: float) -> float:
    """把角度归一到 [-180, 180]，避免角度跳变导致抖动"""
    return (deg + 180.0) % 360.0 - 180.0

def circular_mean_deg(degs) -> float:
    """角度的圆周平均值：例如 179° 和 -179° 的平均应接近 180° 而不是 0°"""
    if not degs:
        return 0.0
    r = np.deg2rad(degs)
    s = float(np.mean(np.sin(r)))
    c = float(np.mean(np.cos(r)))
    return wrap_angle(float(np.rad2deg(np.arctan2(s, c))))
