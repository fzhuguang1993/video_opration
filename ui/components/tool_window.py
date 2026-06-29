# ui/components/tool_window.py
"""通用工具窗口 - 所有工具共用"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent

from tool_config import get_tool


class ToolWindow(QDialog):
    """通用工具窗口"""

    def __init__(self, tool_id: str, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.tool_config = get_tool(tool_id)
        self.view_widget = None
        self.worker = None

        if not self.tool_config:
            raise ValueError(f"未找到工具: {tool_id}")

        self.setWindowTitle(f"{self.tool_config.icon} {self.tool_config.name}")
        # ✅ 根据工具设置不同宽度
        if tool_id == "watermark":
            self.setMinimumSize(600, 800)
        else:
            self.setMinimumSize(1110, 550)
        self.setModal(True)

        self._setup_ui()
        self._load_view()

    def _setup_ui(self):
        """创建通用框架"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel(f"{self.tool_config.icon} {self.tool_config.name}")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 动态内容区域
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_frame, 1)

    def _load_view(self):
        """动态加载对应的视图"""
        from ui.views import get_view_class
        view_class = get_view_class(self.tool_id)
        if view_class:
            self.view_widget = view_class()
            if hasattr(self.view_widget, 'set_user'):
                main_window = self._find_main_window()
                if main_window and hasattr(main_window, 'current_user') and main_window.current_user:
                    self.view_widget.set_user(main_window.current_user)
        else:
            self.view_widget = self._create_placeholder(f"工具: {self.tool_config.name}\n\n开发中...")

        self.content_layout.addWidget(self.view_widget)

    def _find_main_window(self):
        """向上遍历 parent 链查找 MainWindow"""
        from ui.main_window import MainWindow
        widget = self.parent()
        while widget:
            if isinstance(widget, MainWindow):
                return widget
            widget = widget.parent()
        return None

    def _create_placeholder(self, text: str) -> QWidget:
        """创建占位视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #888;")
        layout.addWidget(label)
        return widget

    def closeEvent(self, event: QCloseEvent):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()