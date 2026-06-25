from PySide6.QtWidgets import QPushButton, QMessageBox
from PySide6.QtCore import Qt

class ParamHintButton(QPushButton):
    """带提示的问号按钮"""
    def __init__(self, hint_text, parent=None):
        super().__init__("?", parent)
        self.hint_text = hint_text
        self.setFixedSize(18, 18)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 9px;
                font-weight: bold;
                font-size: 11px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.setToolTip(hint_text)
        self.clicked.connect(self.show_hint)

    def show_hint(self):
        """显示参数提示"""
        QMessageBox.information(self, "参数说明", self.hint_text)