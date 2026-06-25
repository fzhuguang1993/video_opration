from PySide6.QtWidgets import QLabel, QInputDialog, QMessageBox
from PySide6.QtCore import Signal, Qt

class ClickableLabel(QLabel):
    """可点击的标签，双击弹出输入框"""
    value_changed = Signal(int)

    def __init__(self, text="", min_val=0, max_val=9999, is_float=False, parent=None):
        super().__init__(text, parent)
        self.min_val = min_val
        self.max_val = max_val
        self.is_float = is_float
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #f5f6fa;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QLabel:hover {
                background-color: #e8eaf0;
                border-color: #3498db;
            }
        """)
        self.setToolTip("双击输入数值")

    def mouseDoubleClickEvent(self, event):
        if self.is_float:
            current_val = float(self.text())
            value, ok = QInputDialog.getDouble(
                self, "输入数值",
                f"请输入数值 ({self.min_val}-{self.max_val}):",
                current_val, self.min_val, self.max_val, 2
            )
            if ok:
                int_val = int(round(value))
                self.setText(f"{int_val / 100:.2f}")
                self.value_changed.emit(int_val)
        else:
            current_val = int(self.text())
            value, ok = QInputDialog.getInt(
                self, "输入数值",
                f"请输入数值 ({self.min_val}-{self.max_val}):",
                current_val, self.min_val, self.max_val
            )
            if ok:
                self.setText(str(value))
                self.value_changed.emit(value)