"""
REMIND: 通用组件层 (Widgets)
说明：
    这里存放可复用的 UI 小部件 (Components)。
    这些组件功能单一，耦合度低，可以在项目任何地方被重复调用。

包含组件：
    - RoundedImageLabel: 带圆角和抗锯齿的图片显示控件
    - ToastBubble: 类似手机的轻提示气泡 (自动消失)
    - ModalBubble: 强提醒模态弹窗 (跟随视频区域)
    - QuitDialog: 风格化的退出确认对话框
"""

from .bubble import ToastBubble, ModalBubble
from .dialogs import QuitDialog
from .rounded_image_label import RoundedImageLabel