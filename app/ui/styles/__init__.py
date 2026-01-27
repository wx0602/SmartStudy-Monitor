"""
REMIND: 视觉样式层 (Styles)
----------------------------
说明：
    这里存放所有与外观、皮肤、绘图逻辑相关的代码。
    负责管理颜色变量、QSS 样式表以及复杂的自定义绘图。

包含内容：
    - Theme: 定义 Light/Dark 主题的颜色盘
    - BackgroundWidget: 负责绘制主窗口的渐变背景
    - SidebarBackgroundFrame: 负责绘制侧边栏的磨砂/图片背景

"""

from .theme import Theme, theme_by_name, qss, LIGHT, DARK
from .background import BackgroundWidget
from .sidebar_bg import SidebarBackgroundFrame