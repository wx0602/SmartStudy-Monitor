UI 模块说明文档
dashboard_modules 文件夹：存放核心监测数据的可视化卡片组件。
 `focus_card.py` 用于展示专注度评分与疲劳值
 `behavior_card.py` 用于显示违规行为状态，负责将 AI 数据转化为直观的图表反馈。

panels 文件夹：存放右侧侧边栏的功能交互面板。
 `clock.py` 实现计时逻辑，
 `todo_list.py` 处理待办事项的增删改查，
 `controls.py` 用于调节系统灵敏度与音量配置。

widgets 文件夹：存放通用的基础 UI 控件与反馈组件。
`bubble.py` 实现轻量级气泡提示，
`dialogs.py` 实现强力阻断式弹窗，
`rounded_label.py` 等自定义控件，用于构建统一的交互体验。

styles 文件夹：存放界面视觉风格与主题定义。
包含 QSS 样式表与主题配置文件，负责管理亮色/暗色模式的配色方案，以及按钮、背景等控件的全局渲染样式的定义与切换。