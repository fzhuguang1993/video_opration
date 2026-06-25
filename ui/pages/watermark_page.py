# ui/pages/watermark_page.py
"""水印工具页面 - 将原水印功能迁移至此"""
import os
from PySide6.QtWidgets import (
    QFrame,
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QLabel, QFileDialog, QProgressBar, QTextEdit,
    QScrollArea, QGridLayout, QSlider
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTableWidgetItem

from widgets.video_table import VideoTableWidget
from widgets.clickable_label import ClickableLabel
from widgets.param_hint_btn import ParamHintButton
from ui.components.collapsible_params_panel import CollapsibleParamsPanel
from ui.components.tool_panel import ToolPanel
from worker.watermark_worker import WatermarkWorker
from utils.file_utils import get_sorted_video_files
from core.config import get_config
from core.video_service import get_user_video_list
from config import DB_CFG
import pymysql
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QTableWidgetItem

class WatermarkPage(QWidget):
    """水印处理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.worker = None
        self.current_user = None
        self.operator_list = []
        self._setup_ui()

    def set_current_user(self, user_info: dict):
        """设置当前用户"""
        self.current_user = user_info

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # 页面标题
        title = QLabel("🎬 水印工具")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 内容区域
        content = QHBoxLayout()
        content.setSpacing(12)

        left_panel = self._create_left_panel()
        content.addWidget(left_panel)

        right_panel = self._create_right_panel()
        content.addWidget(right_panel, 1)

        layout.addLayout(content)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(440)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setSpacing(8)

        scroll_layout.addWidget(self._create_folder_group())
        scroll_layout.addLayout(self._create_view_buttons())
        scroll_layout.addWidget(self._create_watermark_group())
        scroll_layout.addWidget(self._create_mode_group())
        scroll_layout.addWidget(self._create_watermark_mode_group())
        scroll_layout.addWidget(CollapsibleParamsPanel())
        scroll_layout.addWidget(self._create_control_group())
        scroll_layout.addWidget(ToolPanel())
        scroll_layout.addWidget(self._create_log_panel())
        scroll_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return panel

    def _create_folder_group(self) -> QGroupBox:
        group = QGroupBox("📂 视频文件夹")
        layout = QVBoxLayout()
        row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("选择视频文件夹...")

        folder_btn = QPushButton("📁 浏览")
        folder_btn.setFixedWidth(70)
        folder_btn.clicked.connect(self.select_folder)

        row.addWidget(self.folder_input)
        row.addWidget(folder_btn)
        layout.addLayout(row)
        group.setLayout(layout)
        return group

    def _create_view_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.btn_default_video = QPushButton("本地视频")
        self.btn_my_work = QPushButton("我的作品")
        self.btn_default_video.clicked.connect(self.load_local_videos)
        self.btn_my_work.clicked.connect(self.load_my_works)
        layout.addWidget(self.btn_default_video)
        layout.addWidget(self.btn_my_work)
        return layout

    def _create_watermark_group(self) -> QGroupBox:
        group = QGroupBox("🖼️ 水印图片")
        layout = QVBoxLayout()
        row = QHBoxLayout()
        self.watermark_input = QLineEdit()
        self.watermark_input.setReadOnly(True)
        self.watermark_input.setPlaceholderText("选择水印图片...")
        wm_btn = QPushButton("📁 浏览")
        wm_btn.setFixedWidth(70)
        wm_btn.clicked.connect(self.select_watermark)
        row.addWidget(self.watermark_input)
        row.addWidget(wm_btn)
        layout.addLayout(row)
        group.setLayout(layout)
        return group

    def _create_mode_group(self) -> QGroupBox:
        group = QGroupBox("⚙️ 处理模式")
        layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["选中视频", "前N个", "全部"])
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 999)
        self.count_spin.setValue(1)
        self.count_spin.setEnabled(False)
        self.mode_combo.currentIndexChanged.connect(lambda i: self.count_spin.setEnabled(i == 1))
        layout.addWidget(QLabel("模式:"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(QLabel("N ="))
        layout.addWidget(self.count_spin)
        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_watermark_mode_group(self) -> QGroupBox:
        group = QGroupBox("📍 水印模式")
        layout = QVBoxLayout()
        self.wm_mode_combo = QComboBox()
        self.wm_mode_combo.addItems(["右下角 (固定)", "碰撞反弹", "右下角 + 碰撞反弹"])
        layout.addWidget(self.wm_mode_combo)
        group.setLayout(layout)
        return group

    def _create_control_group(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.start_btn = QPushButton("▶️ 开始处理")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        return widget

    def _create_log_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        log_label = QLabel("📋 处理日志")
        log_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log_text")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(self.config.LOG_PANEL_MAX_HEIGHT)
        self.log_text.setMinimumHeight(self.config.LOG_PANEL_MIN_HEIGHT)
        layout.addWidget(self.log_text)
        return widget

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 运营下拉框（放在这里）
        header = QHBoxLayout()
        header.addWidget(QLabel("📹 视频列表"))
        header.addStretch()
        self.operator_combo = QComboBox()
        self.operator_combo.setFixedWidth(130)
        self.operator_combo.addItem("选择运营", None)
        self.operator_combo.setVisible(False)
        header.addWidget(QLabel("运营:"))
        header.addWidget(self.operator_combo)
        layout.addLayout(header)

        self.video_table = VideoTableWidget(self)
        self.video_table.setMinimumHeight(self.config.VIDEO_TABLE_MIN_HEIGHT)
        layout.addWidget(self.video_table)

        drop_label = QLabel("💡 拖拽视频 | 悬停预览 | 双击重命名/打开")
        drop_label.setStyleSheet("color: #999; font-size: 11px; padding:4px")
        drop_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(drop_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        self.stats_label = QLabel("就绪")
        self.stats_label.setObjectName("stats_label")
        layout.addWidget(self.stats_label)

        return panel

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder:
            self.folder_input.setText(folder)
            self.video_table.load_videos(folder)
            self.update_stats()

    def select_watermark(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.watermark_input.setText(file_path)

    def load_local_videos(self):
        folder = self.folder_input.text().strip()
        if not folder or not os.path.isdir(folder):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先选择视频文件夹")
            return
        self.video_table.view_mode = "local"
        self.video_table.load_videos(folder)
        self.update_stats()
        # 显示运营下拉框
        self.operator_combo.setVisible(True)

    def load_my_works(self):
        try:
            if not self.current_user:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "提示", "未获取登录用户信息")
                return
            user_id = self.current_user["user_id"]
            role = self.current_user["role"]
            is_admin = (role == 1)
            db_video_list = get_user_video_list(user_id, is_admin)

            if not db_video_list:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "提示", "暂无我的作品数据")
                self.video_table.clear_all()
                self.stats_label.setText("📊 共 0 个视频")
                return

            self.video_table.load_my_works_list(db_video_list)
            self.update_stats()
            self.operator_combo.setVisible(False)
        except Exception as e:
            import traceback
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "加载我的作品异常", str(e))

    def update_stats(self):
        total = len(self.video_table.all_videos)
        self.stats_label.setText(f"📊 共 {total} 个视频 | 每页 {self.config.PAGE_SIZE}")

    def load_operator_list(self):
        """加载运营人员列表"""
        conn = None
        cur = None
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            sql = """
            SELECT id, real_name, role
            FROM sys_user 
            WHERE role IN (1, 2)
            ORDER BY role, real_name
            """
            cur.execute(sql)
            results = cur.fetchall()
            self.operator_list = [{"id": r[0], "name": r[1]} for r in results]

            self.operator_combo.clear()
            self.operator_combo.addItem("选择运营", None)
            for op in self.operator_list:
                self.operator_combo.addItem(op["name"], op)

            if self.current_user and self.current_user.get("role") == 2:
                for i in range(self.operator_combo.count()):
                    data = self.operator_combo.itemData(i)
                    if data and data.get("id") == self.current_user.get("user_id"):
                        self.operator_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"加载运营列表失败: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def get_process_params(self) -> dict:
        return {
            'right_margin': 148,
            'bottom_y': 1602,
            'bounce_speed_x': 0.05,
            'bounce_speed_y': 0.05,
            'top_margin': 50,
            'bottom_margin': 50,
            'position_mode': self.wm_mode_combo.currentIndex() + 1
        }

    def start_processing(self):
        input_folder = self.folder_input.text().strip()
        watermark_path = self.watermark_input.text().strip()
        if not input_folder or not os.path.exists(input_folder):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请选择有效的视频文件夹！")
            return
        if not watermark_path or not os.path.exists(watermark_path):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请选择水印图片！")
            return

        mode_index = self.mode_combo.currentIndex()
        params = self.get_process_params()
        video_list = []
        if mode_index == 0:
            video_list = self.video_table.get_selected_videos()
            if not video_list:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "提示", "请勾选视频！")
                return
        elif mode_index == 1:
            all_names = get_sorted_video_files(input_folder)
            take = self.count_spin.value()
            video_list = [os.path.join(input_folder, n) for n in all_names[:take]]

        self.start_btn.setEnabled(False)
        self.worker = WatermarkWorker(
            input_folder=input_folder,
            watermark_path=watermark_path,
            params=params,
            video_list=video_list,
            count_mode='count' if mode_index == 1 else 'all',
            count=self.count_spin.value()
        )
        self.worker.finished.connect(self.on_process_finished)
        self.worker.log.connect(self.on_log_updated)
        self.worker.video_status.connect(self.on_video_status_updated)
        self.worker.start()

    def on_process_finished(self, success: bool, msg: str):
        self.start_btn.setEnabled(True)
        if success:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "完成", msg)
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", msg)

    def on_log_updated(self, log_msg: str):
        print(log_msg)
        self.log_text.append(log_msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def on_video_status_updated(self, video_name: str, status: str):
        table = self.video_table.table
        for row in range(table.rowCount()):
            if self.video_table.view_mode == "local":
                item = table.item(row, 2)
            else:
                item = table.item(row, 4)

            if item and item.text() == video_name:
                status_col = 8 if self.video_table.view_mode == "local" else 7
                status_item = QTableWidgetItem()
                status_item.setTextAlignment(Qt.AlignCenter)

                if status == 'processing':
                    status_item.setText("⏳")
                    status_item.setForeground(QBrush(QColor(243, 156, 18)))
                elif status == 'done':
                    status_item.setText("✅")
                    status_item.setForeground(QBrush(QColor(39, 174, 96)))
                elif status == 'error':
                    status_item.setText("❌")
                    status_item.setForeground(QBrush(QColor(231, 76, 60)))

                table.setItem(row, status_col, status_item)
                break