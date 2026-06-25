import json
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
                               QPushButton, QLabel, QScrollArea, QWidget)
from PySide6.QtCore import Qt
from config import MAX_QUICK_TOOLS, TOOL_CONFIG_FILE
from utils.tools import ALL_TOOLS

class ToolSelectDialog(QDialog):
    def __init__(self, selected_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("全部工具（最多勾选7个）")
        self.setMinimumSize(400, 500)
        self.selected_ids = selected_ids
        self.checkbox_list = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        tip = QLabel(f"提示：最多只能选择 {MAX_QUICK_TOOLS} 个工具显示在首页快捷栏")
        tip.setStyleSheet("color:#e74c3c;")
        layout.addWidget(tip)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll.setWidgetResizable(True)

        for tool_cls in ALL_TOOLS:
            cb = QCheckBox(f"{tool_cls.icon} {tool_cls.name}")
            cb.setToolTip(tool_cls.desc)
            cb.setChecked(tool_cls.tool_id in self.selected_ids)
            cb.tool_id = tool_cls.tool_id
            self.checkbox_list.append(cb)
            scroll_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_select)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # ToolSelectDialog.save_select 内
    def save_select(self):
        # 收集勾选
        choose = [cb.tool_id for cb in self.checkbox_list if cb.isChecked()]
        if len(choose) > MAX_QUICK_TOOLS:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "超限", f"最多只能选择{MAX_QUICK_TOOLS}个！")
            return
        # 直接存数组，不包字典
        with open(TOOL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(choose, f, ensure_ascii=False)
        self.accept()

# 在tool_select_dialog.py中补充
def load_quick_tool_ids():
    """读取本地保存的快捷工具ID列表"""
    if not os.path.exists(TOOL_CONFIG_FILE):
        return []
    try:
        with open(TOOL_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 如果是列表直接返回，如果是字典取数组
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("quick_tool_ids", [])
            else:
                return []
    except Exception as e:
        print(f"加载快捷工具配置失败：{e}")
        return []