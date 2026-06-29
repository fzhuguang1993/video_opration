"""水印工具弹窗"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class WatermarkPreviewDialog(QDialog):
    """水印预览大图弹窗"""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("水印图片预览")
        self.setMinimumSize(400, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: #f8f9fa; border-radius: 4px; padding: 8px;")

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(380, 380, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            label.setFixedSize(scaled.width(), scaled.height())
        else:
            label.setText("无法加载图片")

        layout.addWidget(label)
        layout.setAlignment(label, Qt.AlignCenter)