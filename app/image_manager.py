import os
from pathlib import Path
from PyQt5.QtGui import QPixmap, QIcon

class ImageManager:
    """
    图片资源管理器。
    
    负责统一管理项目中的图片路径，提供 QPixmap 和路径字符串的获取方法。
    """
    def __init__(self):
        # 定位到 assets/images 目录
        self.root = Path(__file__).resolve().parents[1]
        self.img_dir = self.root / "assets" / "images"
        
        # 图片映射表 (Key -> Filename)
        # 即使文件名改了，代码里的 Key (如 'bg_dark') 不用变
        self.image_map = {
            "bg_dark": "dark.jpg",
            "bg_light": "light.jpg",
            "sidebar_dark": "darkbar.jpg",
            "sidebar_light": "lightbar.jpg",
            
            # 你可以在这里继续添加图标...
            # "icon_logo": "logo.png",
        }
        
        # 缓存加载过的 QPixmap，避免重复读取硬盘
        self._cache = {}

    def get_path(self, key: str) -> str:
        """
        根据 key 获取图片的绝对路径字符串。
        如果文件不存在，返回空字符串，防止报错。
        """
        if key not in self.image_map:
            print(f"⚠️ ImageManager: 未定义的图片 Key '{key}'")
            return ""
            
        filename = self.image_map[key]
        path = self.img_dir / filename
        
        if not path.exists():
            print(f"⚠️ ImageManager: 图片文件丢失: {path}")
            return ""
            
        # PyQt 很多组件需要 str 类型的路径
        return str(path)

    def get_pixmap(self, key: str) -> QPixmap:
        """
        根据 key 获取 QPixmap 对象 (带缓存)。
        """
        if key in self._cache:
            return self._cache[key]
            
        path_str = self.get_path(key)
        if not path_str:
            return QPixmap() # 返回空图
            
        pix = QPixmap(path_str)
        self._cache[key] = pix
        return pix

    def get_icon(self, key: str) -> QIcon:
        """
        根据 key 获取 QIcon 对象。
        """
        pix = self.get_pixmap(key)
        return QIcon(pix) if not pix.isNull() else QIcon()

# 全局单例
ImgMgr = ImageManager()