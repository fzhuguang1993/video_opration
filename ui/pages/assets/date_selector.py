# ui/pages/assets/date_selector.py
"""资产管理 - 日期选择器"""
from datetime import datetime, timedelta

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QLabel, QButtonGroup, QWidget
from PySide6.QtCore import Qt


class DateSelector(QWidget):
    """日期范围选择器 - 快捷按钮 + 手动输入"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sync_start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self._sync_end_date = datetime.now().strftime('%Y-%m-%d')
        self._setup_ui()

    @property
    def start_date(self) -> str:
        return self._sync_start_date

    @property
    def end_date(self) -> str:
        return self._sync_end_date

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("📅"))

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._buttons = {}

        for label, days in [("今天", 0), ("昨天", 1), ("近7天", 7), ("近1月", 30), ("近3月", 90)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { padding: 2px 8px; font-size: 12px; border: 1px solid #ddd; border-radius: 4px; }"
                "QPushButton:checked { background: #5e6ad2; color: white; border-color: #5e6ad2; }"
                "QPushButton:hover:!checked { background: #f0f0f5; }"
            )
            btn.clicked.connect(lambda _, d=days: self._on_quick_select(d))
            self._btn_group.addButton(btn)
            layout.addWidget(btn)
            self._buttons[days] = btn

        self._buttons[1].setChecked(True)
        layout.addSpacing(4)

        input_style = (
            "QLineEdit { background: white; color: #333; border: 1px solid #ddd;"
            " border-radius: 4px; padding: 2px 8px; font-size: 12px; }"
            "QLineEdit:focus { border-color: #5e6ad2; }"
        )

        self._start_input = QLineEdit(self._sync_start_date)
        self._start_input.setPlaceholderText("yyyy-MM-dd")
        self._start_input.setFixedSize(100, 28)
        self._start_input.setStyleSheet(input_style)
        self._start_input.textChanged.connect(self._on_manual_change)
        layout.addWidget(self._start_input)

        layout.addWidget(QLabel("→"))

        self._end_input = QLineEdit(self._sync_end_date)
        self._end_input.setPlaceholderText("yyyy-MM-dd")
        self._end_input.setFixedSize(100, 28)
        self._end_input.setStyleSheet(input_style)
        self._end_input.textChanged.connect(self._on_manual_change)
        layout.addWidget(self._end_input)

    def _on_quick_select(self, days: int):
        end = datetime.now()
        start = datetime.now() - timedelta(days=days)
        self._sync_start_date = start.strftime('%Y-%m-%d')
        self._sync_end_date = end.strftime('%Y-%m-%d')
        self._start_input.blockSignals(True)
        self._end_input.blockSignals(True)
        self._start_input.setText(self._sync_start_date)
        self._end_input.setText(self._sync_end_date)
        self._start_input.blockSignals(False)
        self._end_input.blockSignals(False)

    def _on_manual_change(self):
        self._btn_group.setExclusive(False)
        for btn in self._buttons.values():
            btn.setChecked(False)
        self._btn_group.setExclusive(True)
        self._sync_start_date = self._start_input.text().strip()
        self._sync_end_date = self._end_input.text().strip()
