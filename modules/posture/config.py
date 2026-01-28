import os
import yaml

# 定位 thresholds.yaml 的位置
_CUR_DIR = os.path.dirname(__file__) 
_CFG_PATH = os.path.abspath(os.path.join(_CUR_DIR, "../../config/thresholds.yaml"))

def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        print(f"Warning: Configuration file not found at {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return {}

# 加载全局字典
_cfg = _load_yaml(_CFG_PATH)

def cfg_get(key: str, default):
    """从字典获取配置，若无则返回默认值"""
    return _cfg[key] if key in _cfg else default

# 肩膀倾斜
SHOULDER_TILT_THRESH = float(cfg_get("shoulder_tilt", 10.0))

# 头部前伸
HEAD_FORWARD_THRESH  = float(cfg_get("head_forward", 2.0))

# 驼背程度
HUNCHBACK_THRESH     = float(cfg_get("hunchback", 0.25))

# 颈部侧倾
NECK_TILT_THRESH     = float(cfg_get("neck_tilt", 15.0))

# 屏幕距离比例
SCREEN_RATIO_THRESH  = float(cfg_get("screen_distance", 0.5))

# 躯干偏移比例
LEAN_DEGREE_THRESH   = float(cfg_get("lean", 0.15))


def get_posture_config_dict() -> dict:
    """方便外部调试查看"""
    return {
        "SHOULDER_TILT_THRESH": SHOULDER_TILT_THRESH,
        "HEAD_FORWARD_THRESH": HEAD_FORWARD_THRESH,
        "HUNCHBACK_THRESH": HUNCHBACK_THRESH,
        "NECK_TILT_THRESH": NECK_TILT_THRESH,
        "SCREEN_RATIO_THRESH": SCREEN_RATIO_THRESH,
        "LEAN_DEGREE_THRESH": LEAN_DEGREE_THRESH
    }