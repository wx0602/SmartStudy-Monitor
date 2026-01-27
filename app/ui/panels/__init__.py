"""
REMIND: 面板层
说明：
    这里存放应用程序的主要功能面板 (Page/Tab)。
    这些组件通常包含较多的业务逻辑，是用户交互的核心区域。

包含组件：
    - ClockPanel: 时钟、闹钟与番茄钟面板
    - ToDoPanel: 待办事项清单面板
    - ControlsPanel: 参数设置与开关面板
    - HorizontalMonitorBar: 底部数据监控仪表盘
"""

from .clock import ClockPanel
from .controls import ControlsPanel
from .todo_list import ToDoPanel
from .dashboard import HorizontalMonitorBar