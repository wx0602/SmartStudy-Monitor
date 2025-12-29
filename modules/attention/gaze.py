import cv2
import numpy as np

# FaceMesh eye landmarks (stable)
# Left eye: corners (inner=133, outer=33), lids (top=159, bottom=145)
# Right eye: corners (inner=362, outer=263), lids (top=386, bottom=374)
L_CORNER_IN, L_CORNER_OUT = 133, 33
R_CORNER_IN, R_CORNER_OUT = 362, 263
L_TOP, L_BOTTOM = 159, 145
R_TOP, R_BOTTOM = 386, 374

# Eye contour points for polygon mask
LEFT_EYE_POLY = [33, 160, 158, 159, 145, 153, 144, 133]
RIGHT_EYE_POLY = [362, 385, 387, 386, 374, 380, 373, 263]


def _pt(lm, idx, w, h):
    return np.array([lm[idx].x * w, lm[idx].y * h], dtype=np.float32)


def _eye_bbox(poly_pts, margin=6):
    x1 = int(np.min(poly_pts[:, 0])) - margin
    y1 = int(np.min(poly_pts[:, 1])) - margin
    x2 = int(np.max(poly_pts[:, 0])) + margin
    y2 = int(np.max(poly_pts[:, 1])) + margin
    return x1, y1, x2, y2


def _clip_bbox(x1, y1, x2, y2, w, h):
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w - 1, x2))
    y2 = max(0, min(h - 1, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _dark_centroid(gray_roi, mask_roi, dark_percentile=15.0):
    """
    在眼睛 mask 内找“暗区域”质心（近似瞳孔/虹膜暗区）。
    返回 (cx, cy, quality)，坐标在 ROI 坐标系。
    """
    # 将 mask 外设为 255，避免被当成暗区域
    work = gray_roi.copy()
    work[mask_roi == 0] = 255

    # 选取 mask 内像素做阈值
    vals = work[mask_roi > 0]
    if vals.size < 200:
        return None

    thr = np.percentile(vals, dark_percentile)
    bin_dark = (work <= thr).astype(np.uint8) * 255

    # 去噪
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    bin_dark = cv2.morphologyEx(bin_dark, cv2.MORPH_OPEN, k, iterations=1)

    area = int(cv2.countNonZero(bin_dark))
    mask_area = int(cv2.countNonZero(mask_roi))
    if mask_area <= 0:
        return None

    # 质量：暗区占比（太小=找不到，太大=阈值/反光导致整块都黑）
    ratio = area / float(mask_area)
    quality = 0.0
    if 0.01 <= ratio <= 0.35:
        quality = float(1.0 - min(1.0, abs(ratio - 0.12) / 0.12))

    if area < 25:
        min_pos = np.unravel_index(int(np.argmin(work)), work.shape)
        cy, cx = float(min_pos[0]), float(min_pos[1])
        return cx, cy, quality * 0.6

    m = cv2.moments(bin_dark, binaryImage=True)
    if abs(m["m00"]) < 1e-6:
        return None
    cx = float(m["m10"] / m["m00"])
    cy = float(m["m01"] / m["m00"])
    return cx, cy, quality


def _one_eye_gaze(frame_bgr, lm, img_w, img_h, poly_ids, inner_id, outer_id, top_id, bottom_id):
    poly = np.array([_pt(lm, i, img_w, img_h) for i in poly_ids], dtype=np.float32)
    bbox = _eye_bbox(poly, margin=6)
    bbox = _clip_bbox(*bbox, img_w, img_h)
    if bbox is None:
        return None

    x1, y1, x2, y2 = bbox
    if (x2 - x1) < 18 or (y2 - y1) < 10:
        return None

    roi = frame_bgr[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 光照增强
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    # 眼睛多边形
    poly_roi = (poly - np.array([x1, y1], dtype=np.float32)).astype(np.int32)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.fillPoly(mask, [poly_roi], 255)

    res = _dark_centroid(gray, mask, dark_percentile=15.0)
    if res is None:
        return None
    cx, cy, q = res

    # 参考线
    inner = _pt(lm, inner_id, img_w, img_h) - np.array([x1, y1], dtype=np.float32)
    outer = _pt(lm, outer_id, img_w, img_h) - np.array([x1, y1], dtype=np.float32)
    top = _pt(lm, top_id, img_w, img_h) - np.array([x1, y1], dtype=np.float32)
    bottom = _pt(lm, bottom_id, img_w, img_h) - np.array([x1, y1], dtype=np.float32)

    # 防止参考点反了（偶发）
    x_min = float(min(inner[0], outer[0]))
    x_max = float(max(inner[0], outer[0]))
    y_min = float(min(top[1], bottom[1]))
    y_max = float(max(top[1], bottom[1]))

    # 归一化到 [-1,1]，0=居中
    mx = 0.5 * (x_min + x_max)
    hx = max(6.0, 0.5 * (x_max - x_min))
    my = 0.5 * (y_min + y_max)
    hy = max(4.0, 0.5 * (y_max - y_min))

    gx = (float(cx) - mx) / hx
    gy = (float(cy) - my) / hy  # y向下为正：看下方 gy 通常会变正

    gx = float(np.clip(gx, -1.5, 1.5))
    gy = float(np.clip(gy, -1.5, 1.5))
    return gx, gy, q


def calc_gaze_proxy_cv(frame_bgr, lm, img_w, img_h):
    """
    返回 (gx, gy, quality)
    - gx: 左右注视偏移（0=居中，负=偏左，正=偏右）
    - gy: 上下注视偏移（0=居中，负=偏上，正=偏下）
    - quality: 0~1（越大越可信）
    """
    left = _one_eye_gaze(frame_bgr, lm, img_w, img_h,
                        LEFT_EYE_POLY, L_CORNER_IN, L_CORNER_OUT, L_TOP, L_BOTTOM)
    right = _one_eye_gaze(frame_bgr, lm, img_w, img_h,
                          RIGHT_EYE_POLY, R_CORNER_IN, R_CORNER_OUT, R_TOP, R_BOTTOM)

    if left is None and right is None:
        return None

    vals = []
    qs = []
    for item in (left, right):
        if item is None:
            continue
        gx, gy, q = item
        vals.append((gx, gy))
        qs.append(q)

    if not vals:
        return None

    gx = float(np.mean([v[0] for v in vals]))
    gy = float(np.mean([v[1] for v in vals]))
    quality = float(np.mean(qs)) if qs else 0.0

    return gx, gy, quality
