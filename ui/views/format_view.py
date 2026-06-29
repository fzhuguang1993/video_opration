"""视频格式化工具视图 - 占位"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class FormatView(QWidget):
    """视频格式化视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("⚙️ 视频格式化\n\n开发中...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(label)

    def get_params(self) -> dict:
        return {}