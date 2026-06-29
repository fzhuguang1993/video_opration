# utils/tools/trace/widget.py
"""视频溯源工具组件"""

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class TraceDropArea(QLabel):
    """可拖拽区域"""

    files_dropped = Signal(list, list)

    def __init__(self, hint_text: str, min_height: int = 40, parent=None):
        super().__init__(parent)
        self.hint_text = hint_text
        self.setMinimumHeight(min_height)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 6px;
                background: #fafafa;
                color: #9ca3af;
                font-size: 11px;
                padding: 6px;
            }
            QLabel:hover {
                border-color: #5e6ad2;
                background: #f8fafc;
            }
        """)
        self.setText(hint_text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #5e6ad2;
                    border-radius: 6px;
                    background: #eef2ff;
                    color: #5e6ad2;
                    font-size: 11px;
                    padding: 6px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 6px;
                background: #fafafa;
                color: #9ca3af;
                font-size: 11px;
                padding: 6px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 6px;
                background: #fafafa;
                color: #9ca3af;
                font-size: 11px;
                padding: 6px;
            }
        """)
        files = []
        folders = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                folders.append(path)
            elif os.path.isfile(path):
                files.append(path)
        self.files_dropped.emit(files, folders)
