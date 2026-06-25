# ui/pages/settings_page.py
"""系统设置页面 - 占位"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("⚙️")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("系统设置")
        title.setObjectName("page_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("系统设置功能开发中...")
        desc.setObjectName("page_subtitle")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
