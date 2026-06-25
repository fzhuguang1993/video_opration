# widgets/thumbnail_label.py
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal  # ✅ Signal 从 QtCore 导入
from PySide6.QtGui import QPixmap, QMouseEvent
import os
import subprocess


class ThumbnailLabel(QLabel):
    clicked = Signal()  # ✅ 改为 Signal，不是 Signal

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.setFixedSize(50, 32)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)