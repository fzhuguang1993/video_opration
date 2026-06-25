from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit, QWidget,
    QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime

from utils.trace_utils import TraceUtils
from utils.smb_utils import SMBUtils


class TraceWorker(QThread):
    """溯源工作线程"""

    progress = Signal(int)
    log = Signal(str)
    video_status = Signal(str, str)
    finished = Signal(dict)

    def __init__(self, video_paths: list, user_info: dict, upload_to_smb: bool = True):
        super().__init__()
        self.video_paths = video_paths
        self.user_info = user_info
        self.upload_to_smb = upload_to_smb
        self.trace_utils = TraceUtils(user_info)
        self.smb_utils = SMBUtils()
        self._is_cancelled = False

    def cancel(self):
        """取消处理"""
        self._is_cancelled = True

    def run(self):
        """执行溯源任务"""
        results = {
            "total": len(self.video_paths),
            "success": 0,
            "failed": 0,
            "smb_uploaded": 0,
            "smb_failed": 0,
            "details": []
        }

        self.log.emit(f"🚀 开始溯源处理，共 {len(self.video_paths)} 个视频")
        self.log.emit("=" * 50)

        # 定义进度和日志回调
        def progress_callback(value):
            if not self._is_cancelled:
                self.progress.emit(value)

        def log_callback(msg):
            if not self._is_cancelled:
                self.log.emit(msg)

        # 执行处理（带事务管理）
        process_results = self.trace_utils.process_videos(
            self.video_paths,
            operator_name=self.user_info.get("operator_name", self.user_info.get("real_name", "")),
            operator_id=self.user_info.get("operator_id"),
            progress_callback=progress_callback,
            log_callback=log_callback
        )

        # 统计结果
        success_paths = []
        for video_path, result in process_results.items():
            if result["success"]:
                results["success"] += 1
                success_paths.append(result["new_path"])
            else:
                results["failed"] += 1
            results["details"].append(result)

        self.log.emit("=" * 50)
        self.log.emit(f"📊 重命名完成: 成功 {results['success']} 个，失败 {results['failed']} 个")

        # ========== SMB 真实上传 ==========
        if self.upload_to_smb and success_paths and not self._is_cancelled:
            self.log.emit("")
            self.log.emit("📤 开始上传到SMB共享文件夹...")
            self.log.emit("-" * 50)

            # 获取剪辑姓名和运营姓名
            editor_name = self.user_info.get("real_name", "unknown")
            operator_name = self.user_info.get("operator_name", "unknown")
            today = datetime.now().strftime("%Y%m%d")

            # 构建远程路径: 溯源视频/剪辑姓名/日期/运营姓名/
            remote_subpath = f"{editor_name}/{today}/{operator_name}"

            self.log.emit(f"📁 远程路径: {remote_subpath}")

            # 使用真实 SMB 上传
            upload_results = self.smb_utils.upload_files(
                success_paths,
                remote_subpath=remote_subpath,
                log_callback=log_callback
            )

            results["smb_uploaded"] = sum(1 for r in upload_results if r["success"])
            results["smb_failed"] = sum(1 for r in upload_results if not r["success"])

            self.log.emit("-" * 50)
            self.log.emit(f"📤 SMB上传完成: 成功 {results['smb_uploaded']} 个，失败 {results['smb_failed']} 个")
        # ========== SMB 上传结束 ==========

        if self._is_cancelled:
            self.log.emit("")
            self.log.emit("⚠️ 用户取消了操作")
        else:
            self.log.emit("")
            self.log.emit("🎉 全部处理完成！")

        self.finished.emit(results)


class TraceDialog(QDialog):
    """溯源进度对话框"""

    def __init__(self, video_paths: list, user_info: dict, parent=None):
        super().__init__(parent)
        self.video_paths = video_paths
        self.user_info = user_info
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("🔍 溯源处理")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 统计信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"📹 视频数量: {len(self.video_paths)}"))
        info_layout.addWidget(QLabel(f"👤 操作人: {self.user_info.get('real_name', '未知')}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 选项
        options_group = QGroupBox("⚙️ 选项")
        options_layout = QHBoxLayout()
        self.smb_checkbox = QCheckBox("📤 上传到SMB共享文件夹")
        self.smb_checkbox.setChecked(True)
        self.smb_checkbox.setEnabled(False)  # 处理中不可修改
        options_layout.addWidget(self.smb_checkbox)
        options_layout.addStretch()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 22px; }")
        layout.addWidget(self.progress_bar)

        # 日志区域
        log_label = QLabel("📋 处理日志")
        log_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(220)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: Menlo, Consolas, monospace;
                font-size: 11px;
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setEnabled(False)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_processing)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        # 开始处理
        self.start_processing()

    def start_processing(self):
        """开始处理"""
        self.cancel_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = TraceWorker(
            self.video_paths,
            self.user_info,
            upload_to_smb=self.smb_checkbox.isChecked()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def cancel_processing(self):
        """取消处理"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()  # 设置标志位
            self.worker.wait(3000)  # 等待最多3秒让线程优雅退出
            if self.worker.isRunning():
                # 如果3秒后还在运行，才强制终止（万不得已）
                self.worker.terminate()
                self.worker.wait()
            self.append_log("⚠️ 已取消处理")
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)

    def update_progress(self, value: int):
        """更新进度"""
        self.progress_bar.setValue(value)

    def append_log(self, msg: str):
        """追加日志"""
        self.log_text.append(msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def on_finished(self, results: dict):
        """处理完成"""
        self.close_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if results['success'] > 0:
            self.progress_bar.setValue(100)

        self.append_log("")
        self.append_log("=" * 50)
        self.append_log(f"📊 处理结果汇总:")
        self.append_log(f"  总计: {results['total']} 个视频")
        self.append_log(f"  ✅ 成功重命名: {results['success']} 个")
        self.append_log(f"  ❌ 失败: {results['failed']} 个")
        if results.get('smb_uploaded') is not None:
            self.append_log(f"  📤 SMB上传成功: {results['smb_uploaded']} 个")
            self.append_log(f"  📤 SMB上传失败: {results['smb_failed']} 个")