# ui/pages/batch_paste_page.py
"""批量粘贴工具页面"""
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QGroupBox, QLineEdit, QCheckBox,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal

from core.logger import get_logger


class BatchPasteWorker(QThread):
    """批量粘贴工作线程"""
    progress = Signal(int, str)
    finished = Signal(bool, str)
    log = Signal(str)

    def __init__(self, content: str, target_dir: str, prefix: str = "", suffix: str = ""):
        super().__init__()
        self.content = content
        self.target_dir = target_dir
        self.prefix = prefix
        self.suffix = suffix
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            lines = [line.strip() for line in self.content.split('\n') if line.strip()]
            total = len(lines)

            if total == 0:
                self.finished.emit(False, "没有有效内容")
                return

            self.log.emit(f"📋 开始批量处理，共 {total} 条")

            success_count = 0
            for i, line in enumerate(lines):
                if not self._is_running:
                    break

                # 处理每一行
                filename = f"{self.prefix}{line}{self.suffix}"
                filepath = os.path.join(self.target_dir, filename)

                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(line)
                    success_count += 1
                    self.log.emit(f"  ✅ [{i + 1}/{total}] 创建: {filename}")
                except Exception as e:
                    self.log.emit(f"  ❌ [{i + 1}/{total}] 失败: {filename} - {str(e)}")

                self.progress.emit(int((i + 1) / total * 100), f"处理中: {i + 1}/{total}")

            self.finished.emit(True, f"处理完成！成功: {success_count}/{total}")

        except Exception as e:
            self.finished.emit(False, f"错误: {str(e)}")


class BatchPastePage(QWidget):
    """批量粘贴工具页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("batch_paste_page")
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 页面标题
        title = QLabel("📋 批量粘贴工具")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 主内容
        content = QHBoxLayout()
        content.setSpacing(12)

        # 左侧：输入区域
        left_panel = self._create_input_panel()
        content.addWidget(left_panel, 3)

        # 右侧：配置和日志
        right_panel = self._create_right_panel()
        content.addWidget(right_panel, 2)

        layout.addLayout(content)

    def _create_input_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        # 输入框
        input_group = QGroupBox("📝 输入内容")
        input_layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("每行一个数据，批量粘贴到这里...\n\n例如：\n001\n002\n003\n...")
        self.text_input.setMinimumHeight(300)
        input_layout.addWidget(self.text_input)

        # 统计
        self.count_label = QLabel("共 0 行")
        self.count_label.setObjectName("stats_label")
        self.text_input.textChanged.connect(self._update_count)
        input_layout.addWidget(self.count_label)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.process_btn = QPushButton("▶️ 开始处理")
        self.process_btn.setObjectName("primary_btn")
        self.process_btn.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.process_btn)

        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setObjectName("ghost_btn")
        self.clear_btn.clicked.connect(self.text_input.clear)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        # 配置
        config_group = QGroupBox("⚙️ 配置")
        config_layout = QVBoxLayout()

        # 目标目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("目标目录:"))
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(True)
        self.dir_input.setPlaceholderText("选择保存目录...")
        dir_layout.addWidget(self.dir_input)

        dir_btn = QPushButton("📁 浏览")
        dir_btn.setFixedWidth(70)
        dir_btn.clicked.connect(self._select_dir)
        dir_layout.addWidget(dir_btn)
        config_layout.addLayout(dir_layout)

        # 前缀后缀
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("前缀:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("可选")
        prefix_layout.addWidget(self.prefix_input)

        prefix_layout.addWidget(QLabel("后缀:"))
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("可选")
        prefix_layout.addWidget(self.suffix_input)
        config_layout.addLayout(prefix_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 进度条
        progress_group = QGroupBox("📊 进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("就绪")
        self.progress_label.setObjectName("stats_label")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 日志
        log_group = QGroupBox("📋 日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        return panel

    def _update_count(self):
        text = self.text_input.toPlainText()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.count_label.setText(f"共 {len(lines)} 行")

    def _select_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.dir_input.setText(dir_path)

    def _start_processing(self):
        content = self.text_input.toPlainText()
        target_dir = self.dir_input.text().strip()

        if not content.strip():
            QMessageBox.warning(self, "提示", "请输入要粘贴的内容")
            return

        if not target_dir or not os.path.exists(target_dir):
            QMessageBox.warning(self, "提示", "请选择有效的目标目录")
            return

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        reply = QMessageBox.question(
            self,
            "确认处理",
            f"将创建 {len(lines)} 个文件到:\n{target_dir}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        prefix = self.prefix_input.text().strip()
        suffix = self.suffix_input.text().strip()

        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        self.worker = BatchPasteWorker(content, target_dir, prefix, suffix)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, value: int, msg: str):
        self.progress_bar.setValue(value)
        self.progress_label.setText(msg)

    def _on_log(self, msg: str):
        self.log_text.append(msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def _on_finished(self, success: bool, msg: str):
        self.process_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)