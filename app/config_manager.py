import yaml
from pathlib import Path

# 配置管理器类
# 功能：负责读取和保存项目的配置文件 (config/thresholds.yaml)
class ConfigManager:
    def __init__(self):
        # 获取项目根目录 (当前文件父目录的父目录)
        self.root = Path(__file__).resolve().parents[1]
        self.config_path = self.root / "config" / "thresholds.yaml"
        
        # 默认阈值配置 (如果文件不存在，就用这些)
        self.defaults = {
            "shoulder_tilt": 10.0, # 肩膀倾斜阈值 (度)
            "neck_tilt": 15.0,     # 脖子歪斜阈值 (度)
            "head_forward": 0.2,   # 脖子前伸比例阈值 (暂时未启用动态调整)
            "dist_screen": 40.0    # 眼睛离屏幕过近阈值 (cm)
        }
        self.data = self.load_config()

    # 加载配置文件
    def load_config(self):
        if not self.config_path.exists():
            return self.defaults.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                # 合并用户配置和默认配置 (防止用户少写了某一项报错)
                config = self.defaults.copy()
                if user_config:
                    config.update(user_config)
                return config
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")
            return self.defaults.copy()

    # 获取某项配置，如果不存在返回默认值
    def get(self, key, default=None):
        return self.data.get(key, default)

    # (可选) 保存配置
    def save_config(self, new_config):
        self.data.update(new_config)
        try:
            # 确保 config 文件夹存在
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, allow_unicode=True)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")