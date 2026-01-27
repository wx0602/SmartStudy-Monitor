import json
import os
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QCheckBox,
    QWidget
)
from PyQt5.QtCore import Qt


class ToDoPanel(QFrame):
    """
    待办事项面板组件。

    功能特点：
    1. 风格适配：使用 setObjectName("Card") 继承全局卡片样式。
    2. 数据持久化：自动保存任务到 todo.json。
    3. 交互：支持回车添加、勾选完成、点击删除。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.data_file = "todo.json"
        
        # 内部存储结构: [{"text": "任务名", "done": False}, ...]
        self.tasks = []

        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        """初始化界面布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- 标题 ---
        title = QLabel("待办事项")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- 输入区域 ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新任务...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(120, 120, 120, 0.4);
                border-radius: 8px;
                padding: 4px 8px;
                color: #333;
                font-weight: bold;
            }
        """)
        self.input_field.returnPressed.connect(self.add_task)
        input_layout.addWidget(self.input_field)

        btn_add = QPushButton("+")
        btn_add.setFixedSize(32, 32)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 196, 0.2);
                border: 1px solid rgba(59, 130, 196, 0.5);
                border-radius: 8px;
                color: #3B82C4;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(59, 130, 196, 0.4);
            }
        """)
        btn_add.clicked.connect(self.add_task)
        input_layout.addWidget(btn_add)

        layout.addLayout(input_layout)

        # --- 任务列表区域 (滚动) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(5)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

    def add_task(self):
        """添加新任务到列表和数据源。"""
        text = self.input_field.text().strip()
        if not text:
            return

        task_data = {"text": text, "done": False}
        self.tasks.append(task_data)
        self._create_task_widget(task_data)
        
        self.input_field.clear()
        self.save_tasks()

    def _create_task_widget(self, task_data):
        """创建单个任务的 UI 组件行。"""
        item_widget = QFrame()
        item_widget.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }
        """)
        h_layout = QHBoxLayout(item_widget)
        h_layout.setContentsMargins(8, 8, 8, 8)
        
        # 复选框
        chk = QCheckBox()
        chk.setChecked(task_data["done"])
        chk.stateChanged.connect(lambda: self.toggle_task(task_data, chk))
        h_layout.addWidget(chk)

        # 文本标签
        lbl = QLabel(task_data["text"])
        
        # ✅ 核心修改：设置字体加粗
        font = lbl.font()
        font.setBold(True)         # 加粗
        font.setPixelSize(14)      # 字号微调，清晰度更高
        font.setStrikeOut(task_data["done"]) # 保持删除线状态
        lbl.setFont(font)
        
        chk.lbl_ref = lbl 
        h_layout.addWidget(lbl)
        h_layout.addStretch()

        # 删除按钮
        btn_del = QPushButton("×")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #999;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { color: #F0ADA0; }
        """)
        btn_del.clicked.connect(lambda: self.delete_task(task_data, item_widget))
        h_layout.addWidget(btn_del)

        self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)

    def toggle_task(self, task_data, chk):
        """切换任务完成状态。"""
        task_data["done"] = chk.isChecked()
        
        # 更新文字样式 (保留加粗，仅切换删除线)
        font = chk.lbl_ref.font()
        font.setStrikeOut(task_data["done"])
        chk.lbl_ref.setFont(font)
        
        self.save_tasks()

    def delete_task(self, task_data, widget):
        """删除任务。"""
        if task_data in self.tasks:
            self.tasks.remove(task_data)
        
        widget.deleteLater()
        self.save_tasks()

    def load_tasks(self):
        """从 JSON 文件加载任务。"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
                for task in self.tasks:
                    self._create_task_widget(task)
        except Exception as e:
            print(f"加载任务失败: {e}")

    def save_tasks(self):
        """保存任务到 JSON 文件。"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")