import pyautogui
import pyperclip
import time
import platform
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                             QTextEdit, QMessageBox, QProgressBar, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from utils.tools.base_tool import BaseTool


class BatchInputTool(BaseTool):
    tool_id = "batch_input"
    name = "批量粘贴录入"
    icon = "⌨️"
    desc = "复制多行文本，3秒倒计时后自动键鼠批量填入输入框，实时xx/总数进度"

    CONFIG = {
        "DELAY_AFTER_SELECT_ALL": 0.08,
        "DELAY_AFTER_DELETE": 0.06,
        "DELAY_AFTER_PASTE": 0.06,
        "DELAY_BEFORE_ENTER": 0.06,
        "DELAY_AFTER_ENTER": 0.09,
        "CLEAR_INPUT_EVERY_ROW": True,
        "COUNTDOWN_SEC": 3
    }

    def get_mod_key(self):
        return 'command' if platform.system() == "Darwin" else 'ctrl'

    def batch_input_work(self, parent_dialog, line_list):
        mod = self.get_mod_key()
        total = len(line_list)
        progress_bar = parent_dialog.countdown_bar
        progress_text = parent_dialog.countdown_text

        # 重置进度条范围为数据总条数
        progress_bar.setRange(0, total)
        progress_bar.setValue(0)

        for idx, text in enumerate(line_list, 1):
            # ========== 实时刷新 444/999 进度 ==========
            progress_bar.setValue(idx)
            progress_text.setText(f"录入进度：{idx}/{total}")
            # 强制Qt刷新UI，进度实时滚动
            parent_dialog.repaint()
            print(f"录入 {idx}/{total}: {text}")

            if self.CONFIG["CLEAR_INPUT_EVERY_ROW"]:
                pyautogui.hotkey(mod, "a")
                time.sleep(self.CONFIG["DELAY_AFTER_SELECT_ALL"])
                pyautogui.press("delete")
                time.sleep(self.CONFIG["DELAY_AFTER_DELETE"])

            # 备份剪贴板，避免原始剪贴丢失
            backup_clip = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey(mod, "v")
            pyperclip.copy(backup_clip)

            time.sleep(self.CONFIG["DELAY_AFTER_PASTE"])
            pyautogui.press("enter")
            time.sleep(self.CONFIG["DELAY_AFTER_ENTER"])

        # 全部执行完成，不关闭窗口
        progress_text.setText(f"✅ 录入全部完成 {total}/{total}")
        QMessageBox.information(parent_dialog, "完成提示", f"批量录入执行完毕！\n共成功处理 {total} 条数据")

    def run(self):
        # 读取剪贴、过滤空行，修复第一条丢失根源
        raw_lines = pyperclip.paste().splitlines()
        line_list = []
        for line in raw_lines:
            s = line.strip()
            if s:
                line_list.append(s)

        total_lines = len(line_list)
        if total_lines == 0:
            QMessageBox.warning(None, "提示", "剪贴板无有效文本！存在大量空行或乱码")
            return

        # 弹窗主体
        dlg = QDialog()
        dlg.setWindowTitle("批量粘贴录入工具")
        dlg.setFixedSize(460, 300)
        layout = QVBoxLayout(dlg)

        # 红色警告提示
        tip_label = QLabel(
            "⚠️ 重要提醒\n"
            "1. 点击启动后3秒内切换到目标输入框并激活\n"
            "2. 倒计时+录入全程不要切换窗口、移动鼠标、按键盘\n"
            "3. 程序自动操控键鼠批量填充内容"
        )
        tip_label.setStyleSheet("color:#d32f2f;")
        tip_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(tip_label)

        # 文本预览
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setText("\n".join(line_list))
        preview_text.setMaximumHeight(90)
        layout.addWidget(preview_text)

        # 进度条+文字
        self.countdown_bar = QProgressBar()
        self.countdown_bar.setRange(0, self.CONFIG["COUNTDOWN_SEC"])
        self.countdown_bar.setValue(0)
        self.countdown_text = QLabel("等待点击开始...")
        self.countdown_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_bar)
        layout.addWidget(self.countdown_text)

        # 按钮行
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ 启动3秒倒计时")
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # 计时器
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.count_val = self.CONFIG["COUNTDOWN_SEC"]
        dlg.countdown_bar = self.countdown_bar
        dlg.countdown_text = self.countdown_text

        def tick():
            self.count_val -= 1
            self.countdown_bar.setValue(self.CONFIG["COUNTDOWN_SEC"] - self.count_val)
            self.countdown_text.setText(f"跳转窗口倒计时：剩余 {self.count_val} 秒")
            dlg.repaint()
            if self.count_val <= 0:
                self.timer.stop()
                self.start_btn.setEnabled(False)
                self.cancel_btn.setEnabled(False)
                # 不关闭弹窗，直接开始录入
                self.batch_input_work(dlg, line_list)

        def start_countdown():
            self.start_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.count_val = self.CONFIG["COUNTDOWN_SEC"]
            self.countdown_bar.setRange(0, self.CONFIG["COUNTDOWN_SEC"])
            self.countdown_bar.setValue(0)
            self.timer.timeout.connect(tick)
            self.timer.start()

        def cancel_countdown():
            self.timer.stop()
            self.count_val = self.CONFIG["COUNTDOWN_SEC"]
            self.countdown_bar.setValue(0)
            self.countdown_text.setText("倒计时：已手动取消")
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

        self.start_btn.clicked.connect(start_countdown)
        self.cancel_btn.clicked.connect(cancel_countdown)
        dlg.exec()