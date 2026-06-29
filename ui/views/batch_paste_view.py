# ui/views/batch_paste_view.py
"""批量粘贴工具视图"""

import pyautogui
import pyperclip
import platform
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal


class BatchPasteWorker(QThread):
    """批量粘贴后台线程"""

    progress = Signal(int, int, str)  # current, total, text
    finished = Signal(bool, str)
    log = Signal(str)

    def __init__(self, lines: list, config: dict):
        super().__init__()
        self.lines = lines
        self.config = config
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        mod = 'command' if platform.system() == "Darwin" else 'ctrl'
        total = len(self.lines)

        for idx, text in enumerate(self.lines, 1):
            if not self._is_running:
                self.log.emit("⚠️ 用户中断")
                break

            self.progress.emit(idx, total, text)

            # 清空输入框
            if self.config.get("clear_input", True):
                pyautogui.hotkey(mod, "a")
                pyautogui.sleep(self.config.get("delay_select", 0.08))
                pyautogui.press("delete")
                pyautogui.sleep(self.config.get("delay_delete", 0.06))

            # 粘贴
            backup = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey(mod, "v")
            pyautogui.sleep(self.config.get("delay_paste", 0.06))
            pyperclip.copy(backup)

            # 回车
            pyautogui.press("enter")
            pyautogui.sleep(self.config.get("delay_enter", 0.09))

        if self._is_running:
            self.finished.emit(True, f"✅ 录入完成！共 {total} 条")


class BatchPasteView(QWidget):
    """批量粘贴工具视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 说明
        tip = QLabel(
            "📋 批量粘贴录入工具\n"
            "1. 复制多行文本到剪贴板\n"
            "2. 点击「启动」后，3秒内切换到目标输入框\n"
            "3. 程序自动逐行粘贴并回车"
        )
        tip.setStyleSheet("color: #555; font-size: 13px; padding: 8px; background: #f5f5f5; border-radius: 4px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        # 文本预览
        preview_group = QGroupBox("📄 剪贴板预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("点击「读取剪贴板」加载数据...")
        self.preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_text)
        layout.addWidget(preview_group)

        # 读取剪贴板按钮
        read_btn = QPushButton("📋 读取剪贴板")
        read_btn.clicked.connect(self._load_clipboard)
        layout.addWidget(read_btn)

        # 进度
        progress_group = QGroupBox("📊 进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("等待开始...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # 日志
        log_group = QGroupBox("📝 日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        # 按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ 启动（3秒倒计时）")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.clicked.connect(self._start_countdown)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_worker)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 倒计时相关
        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self._tick)
        self.countdown = 3
        self.lines = []

    def _load_clipboard(self):
        """读取剪贴板"""
        text = pyperclip.paste()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        self.lines = lines
        self.preview_text.setText("\n".join(lines))
        self.log_text.append(f"📋 读取到 {len(lines)} 行")
        return lines

    def _start_countdown(self):
        """启动倒计时"""
        if not self.lines:
            QMessageBox.warning(self, "提示", "请先读取剪贴板！")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.countdown = 3
        self.progress_label.setText(f"⏱️ 倒计时 {self.countdown} 秒...")
        self.progress_bar.setValue(0)
        self.log_text.append(f"⏱️ 倒计时 {self.countdown} 秒，请切换到目标输入框...")
        self.countdown_timer.start()

    def _tick(self):
        """倒计时 tick"""
        self.countdown -= 1
        if self.countdown <= 0:
            self.countdown_timer.stop()
            self.progress_label.setText("🚀 开始录入...")
            self.log_text.append("🚀 开始录入...")
            self._start_worker()
        else:
            self.progress_label.setText(f"⏱️ 倒计时 {self.countdown} 秒...")
            self.log_text.append(f"⏱️ {self.countdown}...")

    def _start_worker(self):
        """启动后台线程"""
        config = {
            "clear_input": True,
            "delay_select": 0.08,
            "delay_delete": 0.06,
            "delay_paste": 0.06,
            "delay_enter": 0.09,
        }

        self.worker = BatchPasteWorker(self.lines, config)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.log.connect(self._on_log)
        self.worker.start()
        self.stop_btn.setEnabled(True)

    def _stop_worker(self):
        """停止后台线程"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.log_text.append("⏹️ 已停止")
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)

    def _on_progress(self, current, total, text):
        """进度更新"""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"📝 录入进度：{current}/{total}")

    def _on_finished(self, success, msg):
        """完成"""
        self.progress_label.setText(msg)
        self.log_text.append(msg)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if success:
            self.progress_bar.setValue(100)

    def _on_log(self, msg):
        """日志"""
        self.log_text.append(msg)