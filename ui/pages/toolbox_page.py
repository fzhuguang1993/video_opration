# ui/pages/toolbox_page.py
"""工具箱页面 - 点击工具打开通用窗口"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame
)
from PySide6.QtCore import Qt

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tool_config import get_all_tools
from ui.components.tool_window import ToolWindow


class ToolboxPage(QWidget):
    """工具箱页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("🧰 工具箱")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("选择工具开始使用")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)

        tools = get_all_tools()
        for row, tool in enumerate(tools):
            col = row % 3
            row_idx = row // 3
            card = self._create_tool_card(tool)
            grid.addWidget(card, row_idx, col)

        layout.addLayout(grid)
        layout.addStretch()

    def _create_tool_card(self, tool) -> QFrame:
        card = QFrame()
        card.setObjectName("tool_card")
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)

        icon_label = QLabel(tool.icon)
        icon_label.setObjectName("tool_card_icon")
        layout.addWidget(icon_label)

        name_label = QLabel(tool.name)
        name_label.setObjectName("tool_card_title")
        layout.addWidget(name_label)

        desc_label = QLabel(tool.desc)
        desc_label.setObjectName("tool_card_desc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # ✅ 改成创建 ToolWindow
        def on_click():
            window = ToolWindow(tool.tool_id, self)
            window.exec()

        card.mousePressEvent = lambda e: on_click()

        return card