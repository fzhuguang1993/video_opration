# ui/pages/toolbox_page.py
"""工具箱页面 - 工具卡片网格"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal


class ToolboxPage(QWidget):
    """工具箱页面"""

    tool_selected = Signal(str)  # 工具ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🧰 工具箱")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("选择工具开始使用")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # 工具卡片网格
        grid = QGridLayout()
        grid.setSpacing(16)

        tools = [
            ("🎬", "水印工具", "视频水印添加与处理", "watermark"),
            ("📋", "批量粘贴", "批量数据粘贴工具", "batch_paste"),
            ("🔄", "批量重命名", "批量文件重命名", "rename"),
            ("📦", "格式转换", "视频格式批量转换", "convert"),
            ("⚡", "批量裁剪", "视频批量裁剪", "crop"),
            ("📊", "元数据查看", "视频元数据查看", "metadata"),
        ]

        for row, (icon, name, desc, tool_id) in enumerate(tools):
            col = row % 3
            row_idx = row // 3
            card = self._create_tool_card(icon, name, desc, tool_id)
            grid.addWidget(card, row_idx, col)

        layout.addLayout(grid)
        layout.addStretch()

    def _create_tool_card(self, icon: str, name: str, desc: str, tool_id: str) -> QFrame:
        card = QFrame()
        card.setObjectName("tool_card")
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)

        icon_label = QLabel(icon)
        icon_label.setObjectName("tool_card_icon")
        layout.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setObjectName("tool_card_title")
        layout.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setObjectName("tool_card_desc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # 点击事件
        def on_click():
            self.tool_selected.emit(tool_id)

        card.mousePressEvent = lambda e: on_click()

        return card