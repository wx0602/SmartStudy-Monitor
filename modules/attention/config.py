# 专注度的权重配置文件
import os
import yaml

# 读取 thresholds.yaml
_CUR_DIR = os.path.dirname(__file__) 
_CFG_PATH = os.path.abspath(os.path.join(_CUR_DIR, "../../config/thresholds.yaml"))

def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

_cfg = _load_yaml(_CFG_PATH)

def cfg_get(key: str, default):
    return _cfg[key] if key in _cfg else default


#thresholds

EAR_CLOSED_RATIO = float(cfg_get("EAR_CLOSED_RATIO", 0.45))
EAR_HALF_RATIO   = float(cfg_get("EAR_HALF_RATIO", 0.70))
SLEEPY_TIME      = float(cfg_get("SLEEPY_TIME", 2.0))

YAW_THRESHOLD        = float(cfg_get("YAW_THRESHOLD", 15.0))
PITCH_DOWN_THRESHOLD = float(cfg_get("PITCH_DOWN_THRESHOLD", 12.0))
PITCH_UP_THRESHOLD   = float(cfg_get("PITCH_UP_THRESHOLD", 12.0))
PITCH_DOWN_SIGN      = float(cfg_get("PITCH_DOWN_SIGN", 1))

WINDOW_TIME     = float(cfg_get("WINDOW_TIME", 1.2))
POSE_HOLD_TIME  = float(cfg_get("POSE_HOLD_TIME", 0.4))
ATTN_BAD_THRESHOLD = float(cfg_get("ATTN_BAD_THRESHOLD", 60.0))

FOCAL_SCALE    = float(cfg_get("FOCAL_SCALE", 0.9))
MIN_EYE_DIST   = float(cfg_get("MIN_EYE_DIST", 50.0))
REPROJ_ERR_MAX = float(cfg_get("REPROJ_ERR_MAX", 12.0))
MAX_POSE_JUMP  = float(cfg_get("MAX_POSE_JUMP", 12.0))


CALIB_REPROJ_ERR_MAX = float(cfg_get("CALIB_REPROJ_ERR_MAX", 8.0))

NOFACE_GRACE_SEC = float(cfg_get("NOFACE_GRACE_SEC", 0.4))

# 注意力分数
BLINK_MIN_SEC    = float(cfg_get("BLINK_MIN_SEC", 0.20))
SCORE_EMA_ALPHA  = float(cfg_get("SCORE_EMA_ALPHA", 0.25))

W_EYE    = float(cfg_get("W_EYE", 0.55))
W_AWAY   = float(cfg_get("W_AWAY", 0.20))
W_DOWN   = float(cfg_get("W_DOWN", 0.15))
W_UP     = float(cfg_get("W_UP", 0.05))
W_NOFACE = float(cfg_get("W_NOFACE", 0.25))
W_UNSTB  = float(cfg_get("W_UNSTB", 0.05))

#gaze proxy阈值与权重
GAZE_X_THRESHOLD = float(cfg_get("GAZE_X_THRESHOLD", 0.35))
GAZE_Y_THRESHOLD = float(cfg_get("GAZE_Y_THRESHOLD", 0.40))
GAZE_HOLD_TIME   = float(cfg_get("GAZE_HOLD_TIME", 0.35))
W_GAZE           = float(cfg_get("W_GAZE", 0.15))

YAW_STD_NORM   = float(cfg_get("YAW_STD_NORM", 8.0))
PITCH_STD_NORM = float(cfg_get("PITCH_STD_NORM", 10.0))

def get_config_dict() -> dict:
    return dict(_cfg)
