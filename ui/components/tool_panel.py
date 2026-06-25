# ui/components/tool_panel.py
"""快捷工具箱 - 独立组件"""
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal

from utils.tools import TOOL_MAP
from widgets.tool_select_dialog import ToolSelectDialog, load_quick_tool_ids
from core.config import get_config


class ToolPanel(QGroupBox):
    """快捷工具箱面板"""

    tool_selected = Signal(object)  # 工具对象

    def __init__(self, parent=None):
        super().__init__("🧰 快捷工具箱", parent)
        self.config = get_config()
        self.quick_tool_ids = load_quick_tool_ids()
        self.tool_buttons = []
        self._setup_ui()
        self._refresh_buttons()

    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        self.grid = QGridLayout()
        # ✅ 使用配置中的间距值
        self.grid.setSpacing(self.config.TOOL_GRID_SPACING)
        self.grid.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(self.grid)

        # 设置最小/最大高度 - 使用配置
        self.setMinimumHeight(self.config.TOOL_PANEL_MIN_HEIGHT)
        self.setMaximumHeight(self.config.TOOL_PANEL_MAX_HEIGHT)

    def _refresh_buttons(self):
        """刷新工具按钮"""
        # 清除旧按钮
        for btn in self.tool_buttons:
            btn.deleteLater()
        self.tool_buttons.clear()

        # 清除网格
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加工具按钮（使用配置中的最大数量）
        row = 0
        col = 0
        max_buttons = min(self.config.TOOL_MAX_BUTTONS, len(self.quick_tool_ids))

        for tid in self.quick_tool_ids[:max_buttons]:
            tool_cls = TOOL_MAP.get(tid)
            if not tool_cls:
                continue
            tool_ins = tool_cls()
            btn = QPushButton(f"{tool_ins.icon} {tool_ins.name}")
            btn.setMinimumHeight(self.config.TOOL_BUTTON_MIN_HEIGHT)
            btn.clicked.connect(lambda checked, t=tool_ins: self.tool_selected.emit(t))
            self.grid.addWidget(btn, row, col)
            self.tool_buttons.append(btn)

            col += 1
            if col >= self.config.TOOL_GRID_COLS:  # 使用配置的列数
                col = 0
                row += 1

        # 全部工具按钮
        if col >= self.config.TOOL_GRID_COLS:
            col = 0
            row += 1

        all_tool_btn = QPushButton("📦 全部工具")
        all_tool_btn.setMinimumHeight(self.config.TOOL_BUTTON_MIN_HEIGHT)
        all_tool_btn.clicked.connect(self._open_tool_select)
        self.grid.addWidget(all_tool_btn, row, col)
        self.tool_buttons.append(all_tool_btn)

        # 添加弹簧，保持顶部对齐
        self.grid.setRowStretch(row + 1, 1)

    def _open_tool_select(self):
        """打开工具选择对话框"""
        dlg = ToolSelectDialog(self.quick_tool_ids, self)
        if dlg.exec():
            self.quick_tool_ids = load_quick_tool_ids()
            self._refresh_buttons()

    def set_tools(self, tool_ids: list):
        """设置工具列表"""
        self.quick_tool_ids = tool_ids
        self._refresh_buttons()