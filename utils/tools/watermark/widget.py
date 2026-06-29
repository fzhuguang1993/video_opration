"""水印工具组件"""

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap


class DropArea(QLabel):
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
                border-color: #6366f1;
                background: #f8fafc;
            }
        """)
        self.setText(hint_text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #6366f1;
                    border-radius: 6px;
                    background: #eef2ff;
                    color: #6366f1;
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


class WatermarkThumbnail(QLabel):
    """水印缩略图 - 点击预览"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 45)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                background: #fafafa;
                color: #9ca3af;
                font-size: 10px;
            }
            QLabel:hover {
                border-color: #6366f1;
            }
        """)
        self.setText("无")
        self.setScaledContents(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_image(self, path: str):
        if not path or not os.path.exists(path):
            self.setText("无")
            self.setStyleSheet("""
                QLabel {
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    background: #fafafa;
                    color: #9ca3af;
                    font-size: 10px;
                }
                QLabel:hover {
                    border-color: #6366f1;
                }
            """)
            return

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(60, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #4ade80;
                    border-radius: 4px;
                    background: transparent;
                }
                QLabel:hover {
                    border-color: #6366f1;
                }
            """)
            self.setText("")
        else:
            self.setText("❌")
            self.setStyleSheet("""
                QLabel {
                    border: 1px solid #fca5a5;
                    border-radius: 4px;
                    background: #fef2f2;
                    color: #dc2626;
                    font-size: 10px;
                }
            """)