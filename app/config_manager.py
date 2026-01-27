import sys
import os
import yaml
from pathlib import Path


def resource_path(relative_path):
    """
    获取资源的绝对路径。
    适配开发环境和 PyInstaller 打包后的临时路径 (_MEIPASS)。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ConfigManager:
    """
    配置管理器类
    功能：负责读取和保存项目的配置文件 (config/thresholds.yaml)
    """

    def __init__(self):
        # 使用兼容路径加载配置文件
        self.config_path = Path(resource_path(os.path.join("config", "thresholds.yaml")))

        # ✅ 修复：补全所有模块需要的默认参数
        self.defaults = {
            # 姿态检测
            "shoulder_tilt": 10.0,
            "neck_tilt": 15.0,
            "head_forward": 0.2,
            "dist_screen": 40.0,
            
            # 手部行为 (对应 KeyError: 'hand')
            "hand": {
                "confidence": 0.5,
                "hold_time": 2.0
            },
            
            # 手机检测 (防止 PhoneDetector 报错)
            "phone": {
                "confidence": 0.5
            },
            
            # 离席检测 (防止 SeatDetector 报错)
            "seat": {
                "check_interval": 30
            }
        }
        self.data = self.load_config()

    def load_config(self):
        """加载配置文件。"""
        # 1. 尝试从资源路径加载
        if not self.config_path.exists():
            # 2. 如果资源路径没有，尝试从本地运行目录加载
            local_path = Path("config/thresholds.yaml")
            if local_path.exists():
                self.config_path = local_path
            else:
                print("Warning: Configuration file not found, using defaults.")
                return self.defaults.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                # 合并用户配置和默认配置 (防止用户少写了某一项报错)
                config = self.defaults.copy()
                if user_config:
                    # 递归更新字典（简单的 update 可能覆盖掉子字典）
                    for k, v in user_config.items():
                        if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                            config[k].update(v)
                        else:
                            config[k] = v
                return config
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}，使用默认配置。")
            return self.defaults.copy()

    def get(self, key, default=None):
        """获取某项配置，如果不存在返回默认值。"""
        return self.data.get(key, default)

    def save_config(self, new_config):
        """(可选) 保存配置。"""
        self.data.update(new_config)
        try:
            # 确保 config 文件夹存在
            if not self.config_path.parent.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, allow_unicode=True)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")