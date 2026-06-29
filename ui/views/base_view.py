# ui/views/base_view.py
"""工具视图基类"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class BaseToolView(QWidget):
    """工具视图基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """子类重写"""
        pass

    def get_params(self) -> dict:
        """获取参数，子类重写"""
        return {}

    def set_log(self, msg: str):
        """显示日志"""
        pass