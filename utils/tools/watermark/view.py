"""水印工具视图 - 无预览版"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QFileDialog,
    QMessageBox, QProgressDialog, QSlider, QGridLayout
)
from PySide6.QtCore import Qt

from .widget import DropArea, WatermarkThumbnail
from .dialog import WatermarkPreviewDialog
from .worker import WatermarkWorker


class WatermarkView(QWidget):
    """水印工具视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_files = []
        self.watermark_path = ""
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 视频源
        video_group = QGroupBox("📹 视频源")
        video_layout = QVBoxLayout(video_group)
        video_layout.setSpacing(4)

        self.video_drop = DropArea("拖拽视频或文件夹到此", min_height=60)
        self.video_drop.files_dropped.connect(self._on_video_dropped)
        video_layout.addWidget(self.video_drop)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.select_folder_btn = QPushButton("📁 选择文件夹")
        self.select_folder_btn.clicked.connect(self._select_video_folder)
        btn_row.addWidget(self.select_folder_btn)

        self.select_files_btn = QPushButton("📄 选择文件")
        self.select_files_btn.clicked.connect(self._select_video_files)
        btn_row.addWidget(self.select_files_btn)

        self.clear_video_btn = QPushButton("🗑️ 清空")
        self.clear_video_btn.clicked.connect(self._clear_video_list)
        btn_row.addWidget(self.clear_video_btn)

        btn_row.addStretch()
        video_layout.addLayout(btn_row)

        self.video_count = QLabel("共 0 个视频")
        self.video_count.setStyleSheet("color: #6b7280; font-size: 12px;")
        video_layout.addWidget(self.video_count)

        main_layout.addWidget(video_group)

        # 水印图片
        wm_group = QGroupBox("🖼️ 水印图片")
        wm_layout = QHBoxLayout(wm_group)
        wm_layout.setSpacing(8)

        self.wm_drop = DropArea("拖拽图片到此", min_height=50)
        self.wm_drop.files_dropped.connect(self._on_watermark_dropped)
        wm_layout.addWidget(self.wm_drop, 2)

        self.wm_thumbnail = WatermarkThumbnail()
        self.wm_thumbnail.clicked.connect(self._preview_watermark)
        wm_layout.addWidget(self.wm_thumbnail)

        wm_btn_layout = QVBoxLayout()
        wm_btn_layout.setSpacing(3)
        self.select_wm_btn = QPushButton("选择")
        self.select_wm_btn.clicked.connect(self._select_watermark)
        wm_btn_layout.addWidget(self.select_wm_btn)
        self.clear_wm_btn = QPushButton("清除")
        self.clear_wm_btn.clicked.connect(self._clear_watermark)
        wm_btn_layout.addWidget(self.clear_wm_btn)
        wm_layout.addLayout(wm_btn_layout)

        main_layout.addWidget(wm_group)

        # ===== 水印参数 + 参数校准 并排 =====
        param_row_layout = QHBoxLayout()
        param_row_layout.setSpacing(16)

        # --- 水印参数（左） ---
        param_group = QGroupBox("⚙️ 水印参数")
        param_layout = QVBoxLayout(param_group)
        param_layout.setSpacing(6)

        def add_param_row(parent_layout, label_text, spinbox, slider):
            row = QHBoxLayout()
            row.setSpacing(4)
            label = QLabel(label_text)
            label.setFixedWidth(50)
            row.addWidget(label)
            spinbox.setFixedWidth(60)
            row.addWidget(spinbox)
            slider.setFixedWidth(80)
            row.addWidget(slider)
            row.addStretch()
            parent_layout.addLayout(row)

        # 模式
        row0 = QHBoxLayout()
        row0.setSpacing(4)
        row0.addWidget(QLabel("模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["右下角固定", "碰撞反弹", "右下+碰撞"])
        self.mode_combo.setFixedWidth(120)
        row0.addWidget(self.mode_combo)
        row0.addStretch()
        param_layout.addLayout(row0)

        # 右边距
        self.right_margin = QSpinBox()
        self.right_margin.setRange(0, 500)
        self.right_margin.setValue(148)
        self.right_margin.setButtonSymbols(QSpinBox.NoButtons)
        self.right_margin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QSpinBox:focus { border-color: #6366f1; }
        """)
        self.right_margin.valueChanged.connect(self._update_preview)
        self.right_margin_slider = QSlider(Qt.Horizontal)
        self.right_margin_slider.setRange(0, 500)
        self.right_margin_slider.setValue(148)
        self.right_margin_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.right_margin_slider.valueChanged.connect(self.right_margin.setValue)
        self.right_margin.valueChanged.connect(self.right_margin_slider.setValue)
        add_param_row(param_layout, "右边距:", self.right_margin, self.right_margin_slider)

        # 底部Y
        self.bottom_y = QSpinBox()
        self.bottom_y.setRange(0, 2000)
        self.bottom_y.setValue(1602)
        self.bottom_y.setButtonSymbols(QSpinBox.NoButtons)
        self.bottom_y.setStyleSheet("""
            QSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QSpinBox:focus { border-color: #6366f1; }
        """)
        self.bottom_y.valueChanged.connect(self._update_preview)
        self.bottom_y_slider = QSlider(Qt.Horizontal)
        self.bottom_y_slider.setRange(0, 2000)
        self.bottom_y_slider.setValue(1602)
        self.bottom_y_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.bottom_y_slider.valueChanged.connect(self.bottom_y.setValue)
        self.bottom_y.valueChanged.connect(self.bottom_y_slider.setValue)
        add_param_row(param_layout, "底部Y:", self.bottom_y, self.bottom_y_slider)

        # 速度X
        self.speed_x = QDoubleSpinBox()
        self.speed_x.setRange(0.01, 1.0)
        self.speed_x.setSingleStep(0.01)
        self.speed_x.setValue(0.05)
        self.speed_x.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.speed_x.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QDoubleSpinBox:focus { border-color: #6366f1; }
        """)
        self.speed_x_slider = QSlider(Qt.Horizontal)
        self.speed_x_slider.setRange(1, 100)
        self.speed_x_slider.setValue(5)
        self.speed_x_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.speed_x_slider.valueChanged.connect(lambda v: self.speed_x.setValue(v / 100))
        self.speed_x.valueChanged.connect(lambda v: self.speed_x_slider.setValue(int(v * 100)))
        add_param_row(param_layout, "速度X:", self.speed_x, self.speed_x_slider)

        # 速度Y
        self.speed_y = QDoubleSpinBox()
        self.speed_y.setRange(0.01, 1.0)
        self.speed_y.setSingleStep(0.01)
        self.speed_y.setValue(0.05)
        self.speed_y.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.speed_y.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QDoubleSpinBox:focus { border-color: #6366f1; }
        """)
        self.speed_y_slider = QSlider(Qt.Horizontal)
        self.speed_y_slider.setRange(1, 100)
        self.speed_y_slider.setValue(5)
        self.speed_y_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.speed_y_slider.valueChanged.connect(lambda v: self.speed_y.setValue(v / 100))
        self.speed_y.valueChanged.connect(lambda v: self.speed_y_slider.setValue(int(v * 100)))
        add_param_row(param_layout, "速度Y:", self.speed_y, self.speed_y_slider)

        # 顶部边距
        self.top_margin = QSpinBox()
        self.top_margin.setRange(0, 500)
        self.top_margin.setValue(50)
        self.top_margin.setButtonSymbols(QSpinBox.NoButtons)
        self.top_margin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QSpinBox:focus { border-color: #6366f1; }
        """)
        self.top_margin.valueChanged.connect(self._update_preview)
        self.top_margin_slider = QSlider(Qt.Horizontal)
        self.top_margin_slider.setRange(0, 500)
        self.top_margin_slider.setValue(50)
        self.top_margin_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.top_margin_slider.valueChanged.connect(self.top_margin.setValue)
        self.top_margin.valueChanged.connect(self.top_margin_slider.setValue)
        add_param_row(param_layout, "顶边距:", self.top_margin, self.top_margin_slider)

        # 底部边距
        self.bottom_margin = QSpinBox()
        self.bottom_margin.setRange(0, 500)
        self.bottom_margin.setValue(50)
        self.bottom_margin.setButtonSymbols(QSpinBox.NoButtons)
        self.bottom_margin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: #f8fafc;
                padding: 2px 4px;
                font-weight: 500;
                color: #1f2937;
            }
            QSpinBox:focus { border-color: #6366f1; }
        """)
        self.bottom_margin.valueChanged.connect(self._update_preview)
        self.bottom_margin_slider = QSlider(Qt.Horizontal)
        self.bottom_margin_slider.setRange(0, 500)
        self.bottom_margin_slider.setValue(50)
        self.bottom_margin_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #e5e7eb; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6366f1; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #4f46e5; }
        """)
        self.bottom_margin_slider.valueChanged.connect(self.bottom_margin.setValue)
        self.bottom_margin.valueChanged.connect(self.bottom_margin_slider.setValue)
        add_param_row(param_layout, "底边距:", self.bottom_margin, self.bottom_margin_slider)

        param_row_layout.addWidget(param_group, 1)

        # --- 参数校准（右） ---
        calibrate_group = QGroupBox("🎯 参数校准")
        calibrate_layout = QVBoxLayout(calibrate_group)
        calibrate_layout.setSpacing(6)

        # 视频码率
        row_vbr = QHBoxLayout()
        row_vbr.setSpacing(4)
        row_vbr.addWidget(QLabel("视频码率:"))
        self.video_bitrate = QComboBox()
        self.video_bitrate.addItems(["2M", "4M", "6M", "8M", "10M", "12M", "16M"])
        self.video_bitrate.setCurrentText("4M")
        self.video_bitrate.setFixedWidth(80)
        row_vbr.addWidget(self.video_bitrate)
        row_vbr.addStretch()
        calibrate_layout.addLayout(row_vbr)

        # 音频码率
        row_abr = QHBoxLayout()
        row_abr.setSpacing(4)
        row_abr.addWidget(QLabel("音频码率:"))
        self.audio_bitrate = QComboBox()
        self.audio_bitrate.addItems(["32k", "44k", "64k", "96k", "128k", "192k", "256k"])
        self.audio_bitrate.setCurrentText("44k")
        self.audio_bitrate.setFixedWidth(80)
        row_abr.addWidget(self.audio_bitrate)
        row_abr.addStretch()
        calibrate_layout.addLayout(row_abr)

        # 帧率
        row_fps = QHBoxLayout()
        row_fps.setSpacing(4)
        row_fps.addWidget(QLabel("帧率:"))
        self.fps = QComboBox()
        self.fps.addItems(["24", "25", "30", "50", "60"])
        self.fps.setCurrentText("30")
        self.fps.setFixedWidth(80)
        row_fps.addWidget(self.fps)
        row_fps.addStretch()
        calibrate_layout.addLayout(row_fps)

        # 分辨率
        row_res = QHBoxLayout()
        row_res.setSpacing(4)
        row_res.addWidget(QLabel("分辨率:"))
        self.resolution = QComboBox()
        self.resolution.addItems([
            "1920x1080 (1080p)",
            "1280x720 (720p)",
            "1080x1920 (1080p竖屏)",
            "720x1280 (720p竖屏)",
            "3840x2160 (4K)",
            "1920x1920 (1:1)",
            "1080x1080 (1:1)"
        ])
        self.resolution.setCurrentText("1080x1920 (1080p竖屏)")
        self.resolution.setFixedWidth(160)
        row_res.addWidget(self.resolution)
        row_res.addStretch()
        calibrate_layout.addLayout(row_res)

        # 平台预设
        row_platform = QHBoxLayout()
        row_platform.setSpacing(4)
        row_platform.addWidget(QLabel("平台预设:"))
        self.platform_preset = QComboBox()
        self.platform_preset.addItems(["自定义", "抖音", "快手", "小红书", "视频号", "腾讯信息流"])
        self.platform_preset.setCurrentText("自定义")
        self.platform_preset.setFixedWidth(120)
        self.platform_preset.currentTextChanged.connect(self._apply_platform_preset)
        row_platform.addWidget(self.platform_preset)
        row_platform.addStretch()
        calibrate_layout.addLayout(row_platform)

        param_row_layout.addWidget(calibrate_group, 1)

        main_layout.addLayout(param_row_layout)

        # 执行按钮
        btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("▶ 执行水印处理")
        self.execute_btn.setObjectName("primary_btn")
        self.execute_btn.clicked.connect(self._execute)
        btn_layout.addWidget(self.execute_btn)

        self.close_btn = QPushButton("✕ 关闭")
        self.close_btn.clicked.connect(self._close_window)
        btn_layout.addWidget(self.close_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def _apply_platform_preset(self, platform: str):
        """应用平台预设参数"""
        presets = {
            "抖音": {"video": "6M", "audio": "128k", "fps": "30", "res": "1080x1920 (1080p竖屏)"},
            "快手": {"video": "4M", "audio": "64k", "fps": "30", "res": "1080x1920 (1080p竖屏)"},
            "小红书": {"video": "8M", "audio": "128k", "fps": "30", "res": "1080x1920 (1080p竖屏)"},
            "视频号": {"video": "4M", "audio": "64k", "fps": "25", "res": "1280x720 (720p)"},
            "腾讯信息流": {"video": "6M", "audio": "96k", "fps": "30", "res": "1280x720 (720p)"},
        }
        if platform in presets:
            p = presets[platform]
            self.video_bitrate.setCurrentText(p["video"])
            self.audio_bitrate.setCurrentText(p["audio"])
            self.fps.setCurrentText(p["fps"])
            self.resolution.setCurrentText(p["res"])

    def _update_preview(self):
        pass

    def _on_video_dropped(self, files: list, folders: list):
        for folder in folders:
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        self.video_files.append(os.path.join(root, f))
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                if file not in self.video_files:
                    self.video_files.append(file)
        self._update_video_count()

    def _select_video_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder:
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        self.video_files.append(os.path.join(root, f))
            self._update_video_count()

    def _select_video_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv)"
        )
        for path in paths:
            if path not in self.video_files:
                self.video_files.append(path)
        self._update_video_count()

    def _clear_video_list(self):
        self.video_files = []
        self._update_video_count()

    def _update_video_count(self):
        self.video_count.setText(f"共 {len(self.video_files)} 个视频")

    def _on_watermark_dropped(self, files: list, folders: list):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.watermark_path = f
                self.wm_thumbnail.set_image(f)
                break

    def _select_watermark(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.watermark_path = path
            self.wm_thumbnail.set_image(path)

    def _clear_watermark(self):
        self.watermark_path = ""
        self.wm_thumbnail.set_image("")

    def _preview_watermark(self):
        if self.watermark_path and os.path.exists(self.watermark_path):
            dialog = WatermarkPreviewDialog(self.watermark_path, self)
            dialog.exec()

    def _close_window(self):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "正在处理中，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                self.window().close()
        else:
            self.window().close()

    def _execute(self):
        if not self.video_files:
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return

        # 如果有水印但文件不存在，提示
        if self.watermark_path and not os.path.exists(self.watermark_path):
            QMessageBox.warning(self, "提示", f"水印图片不存在,仅处理视频格式")
            return

        # 如果没有水印，正常执行（只做转码）

        params = {
            'mode': self.mode_combo.currentIndex() + 1,
            'right_margin': self.right_margin.value(),
            'bottom_y': self.bottom_y.value(),
            'speed_x': self.speed_x.value(),
            'speed_y': self.speed_y.value(),
            'top_margin': self.top_margin.value(),
            'bottom_margin': self.bottom_margin.value(),
            'video_bitrate': self.video_bitrate.currentText(),
            'audio_bitrate': self.audio_bitrate.currentText(),
            'fps': self.fps.currentText(),
            'resolution': self.resolution.currentText(),
        }

        self.execute_btn.setEnabled(False)

        progress = QProgressDialog("正在处理...", "取消", 0, len(self.video_files), self)
        progress.setWindowTitle("水印处理")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        self.worker = WatermarkWorker(self.video_files, self.watermark_path, params)
        self.worker.progress.connect(lambda c, t, n: progress.setValue(c))
        self.worker.finished.connect(lambda s, m: self._on_finished(s, m, progress))
        self.worker.start()

    def _on_finished(self, success, msg, progress):
        progress.close()
        self.execute_btn.setEnabled(True)
        QMessageBox.information(self, "完成", msg)