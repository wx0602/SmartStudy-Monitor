import cv2
import numpy as np

try:
    import mediapipe as mp
    _mp_selfie = mp.solutions.selfie_segmentation
except Exception:
    _mp_selfie = None


class BackgroundBlur:
    """
    人像背景虚化（带主题差异）
    - theme: "light" / "dark"
    """
    def __init__(self, theme: str = "light"):
        self.theme = theme
        self.enabled = True

        self._segmenter = None
        if _mp_selfie is not None:
            # model_selection=1 一般更稳一点（人像）
            self._segmenter = _mp_selfie.SelfieSegmentation(model_selection=1)

    def set_theme(self, theme: str):
        self.theme = theme or "light"

    def set_enabled(self, on: bool):
        self.enabled = bool(on)

    def apply(self, frame_bgr: np.ndarray) -> np.ndarray:
        if not self.enabled or self._segmenter is None:
            return frame_bgr

        h, w = frame_bgr.shape[:2]

        # 1) segmentation mask
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self._segmenter.process(rgb)
        if res.segmentation_mask is None:
            return frame_bgr

        mask = res.segmentation_mask  # float32 [0..1]
        # 2) 根据主题设置阈值 / 羽化
        if self.theme == "dark":
            thresh = 0.55
            feather = 17   # 羽化更强一点，暗色更“融”
            blur_ks = 61   # 背景更糊，风格更强
            tint = (18, 28, 44)  # BGR 冷蓝黑
            tint_alpha = 0.18
            bg_gamma = 0.92      # 背景略压暗
        else:
            thresh = 0.60
            feather = 13
            blur_ks = 45
            tint = (235, 245, 255)  # BGR 轻白蓝
            tint_alpha = 0.12
            bg_gamma = 1.02         # 背景略提亮

        # 二值化 + 羽化（soft mask）
        m = (mask > thresh).astype(np.float32)
        m = cv2.GaussianBlur(m, (feather, feather), 0)
        m = np.clip(m, 0.0, 1.0)[..., None]  # HxWx1

        # 3) 背景虚化
        k = blur_ks if blur_ks % 2 == 1 else blur_ks + 1
        bg_blur = cv2.GaussianBlur(frame_bgr, (k, k), 0)

        # 4) 背景色调玻璃层（让明暗差异更明显）
        tint_layer = np.full_like(bg_blur, tint, dtype=np.uint8)
        bg_styled = cv2.addWeighted(bg_blur, 1.0 - tint_alpha, tint_layer, tint_alpha, 0)

        # 5) 背景亮度微调（gamma）
        bg_styled = np.clip(((bg_styled / 255.0) ** (1.0 / bg_gamma)) * 255.0, 0, 255).astype(np.uint8)

        # 6) 合成：前景保持清晰，背景用 styled blur
        out = frame_bgr.astype(np.float32) * m + bg_styled.astype(np.float32) * (1.0 - m)
        return out.astype(np.uint8)
