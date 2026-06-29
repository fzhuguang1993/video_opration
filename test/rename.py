# ui/views/rename_view.py
"""批量重命名工具视图 - 拖拽版"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QSpinBox,
    QFileDialog, QGroupBox, QMessageBox, QFrame,
    QDialog, QDialogButtonBox, QScrollArea, QSizePolicy,
    QMenu, QCheckBox, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal


class NumberFormatDialog(QDialog):
    """编号格式设置弹窗"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("编号格式设置")
        self.setFixedSize(380, 200)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; }
            QLabel { color: #333; }
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #5e6ad2;
            }
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton[default="true"] {
                background: #5e6ad2;
                color: white;
            }
            QPushButton[default="true"]:hover {
                background: #4a56c2;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 编号类型
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("编号类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "数字 (1, 2, 3...)",
            "大写字母 (A, B, C...)",
            "小写字母 (a, b, c...)",
            "罗马数字 (I, II, III...)",
            "希腊字母 (α, β, γ...)"
        ])
        self.type_combo.setFixedWidth(200)
        row1.addWidget(self.type_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 起始值
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("起始值:"))
        self.start_input = QLineEdit()
        self.start_input.setFixedWidth(150)
        self.start_input.setPlaceholderText("1 或 A 或 I")
        row2.addWidget(self.start_input)
        row2.addStretch()
        layout.addLayout(row2)

        # 结束值
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("结束值:"))
        self.end_input = QLineEdit()
        self.end_input.setFixedWidth(150)
        self.end_input.setPlaceholderText("100 或 Z 或 X")
        row3.addWidget(self.end_input)
        row3.addStretch()
        layout.addLayout(row3)

        # 位数
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("编号位数:"))
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(1, 6)
        self.padding_spin.setValue(3)
        self.padding_spin.setFixedWidth(80)
        row4.addWidget(self.padding_spin)
        row4.addStretch()
        layout.addLayout(row4)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("确定")
        ok_btn.setProperty("default", True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        if config:
            self._load_config(config)

    def _load_config(self, config):
        type_map = {
            "数字": 0, "大写字母": 1, "小写字母": 2,
            "罗马数字": 3, "希腊字母": 4
        }
        self.type_combo.setCurrentIndex(type_map.get(config.get('type', '数字'), 0))
        self.start_input.setText(config.get('start', '1'))
        self.end_input.setText(config.get('end', '100'))
        self.padding_spin.setValue(config.get('padding', 3))

    def get_config(self):
        type_name = self.type_combo.currentText()
        type_map = {
            "数字 (1, 2, 3...)": "数字",
            "大写字母 (A, B, C...)": "大写字母",
            "小写字母 (a, b, c...)": "小写字母",
            "罗马数字 (I, II, III...)": "罗马数字",
            "希腊字母 (α, β, γ...)": "希腊字母"
        }
        return {
            'type': type_map.get(type_name, "数字"),
            'start': self.start_input.text().strip(),
            'end': self.end_input.text().strip(),
            'padding': self.padding_spin.value(),
        }


class RuleBlock(QFrame):
    changed = Signal()
    remove_requested = Signal(object)
    edit_requested = Signal(object)

    def __init__(self, block_type="固定", default_text="", removable=True, parent=None):
        super().__init__(parent)
        self.block_type = block_type
        self.is_editing = False
        self.removable = removable
        self.number_config = None
        self._setup_ui(default_text)
        self._update_style()

    def _setup_ui(self, default_text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 6, 2)
        layout.setSpacing(2)

        self.type_label = QLabel(self.block_type)
        self.type_label.setStyleSheet("font-size: 10px; color: #888;")
        self.type_label.setFixedWidth(28)
        layout.addWidget(self.type_label)

        self.display_label = QLabel(default_text or "点击编辑")
        self.display_label.setStyleSheet("""
            font-size: 13px; padding: 2px 8px; border-radius: 3px;
            border: 1px solid #ddd; background: #f5f5f5;
        """)
        self.display_label.setFixedWidth(100)
        self.display_label.mousePressEvent = self._start_edit
        layout.addWidget(self.display_label)

        self.edit_input = QLineEdit(default_text)
        self.edit_input.setFixedWidth(100)
        self.edit_input.setVisible(False)
        self.edit_input.returnPressed.connect(self._finish_edit)
        self.edit_input.editingFinished.connect(self._finish_edit)
        layout.addWidget(self.edit_input)

        if self.block_type == "编号":
            self.menu_btn = QPushButton("●")
            self.menu_btn.setFixedSize(24, 24)
            self.menu_btn.setStyleSheet("""
                QPushButton {
                    background: #5e6ad2; color: white; border: none;
                    border-radius: 12px; font-size: 10px;
                }
                QPushButton:hover { background: #4a56c2; }
            """)
            self.menu_btn.clicked.connect(self._show_menu)
            layout.addWidget(self.menu_btn)
        elif not self.removable:
            lock_label = QLabel("🔒")
            lock_label.setStyleSheet("font-size: 12px; color: #999;")
            layout.addWidget(lock_label)
        else:
            self.remove_btn = QPushButton("✕")
            self.remove_btn.setFixedSize(18, 18)
            self.remove_btn.setStyleSheet("""
                QPushButton {
                    background: #e74c3c; color: white; border: none;
                    border-radius: 9px; font-size: 10px; padding: 0px;
                }
                QPushButton:hover { background: #c0392b; }
            """)
            self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
            layout.addWidget(self.remove_btn)

        self.setFixedHeight(34)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 16px; border-radius: 4px; }
            QMenu::item:selected { background: #eef0ff; }
        """)
        edit_action = menu.addAction("✎ 编辑")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self))
        delete_action = menu.addAction("✕ 删除")
        delete_action.triggered.connect(lambda: self.remove_requested.emit(self))
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())
        menu.exec(pos)

    def _update_style(self):
        if self.is_editing:
            self.display_label.setStyleSheet("""
                font-size: 13px; padding: 2px 8px; border-radius: 3px;
                border: 2px solid #5e6ad2; background: #eef0ff;
            """)
        else:
            self.display_label.setStyleSheet("""
                font-size: 13px; padding: 2px 8px; border-radius: 3px;
                border: 1px solid #ddd; background: #f5f5f5;
            """)

    def _start_edit(self, event):
        if self.block_type == "扩展名":
            return
        self.is_editing = True
        self.display_label.setVisible(False)
        self.edit_input.setVisible(True)
        self.edit_input.setFocus()
        self.edit_input.selectAll()
        self._update_style()

    def _finish_edit(self):
        self.is_editing = False
        text = self.edit_input.text().strip()
        if not text:
            text = "点击编辑"
        self.display_label.setText(text)
        self.edit_input.setVisible(False)
        self.display_label.setVisible(True)
        self._update_style()
        self.changed.emit()

    def get_text(self) -> str:
        if self.is_editing:
            return self.edit_input.text().strip()
        return self.display_label.text()

    def set_text(self, text: str):
        self.display_label.setText(text)
        self.edit_input.setText(text)
        self.changed.emit()


class RenameWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(bool, str)

    def __init__(self, file_paths: list, pattern: list):
        super().__init__()
        self.file_paths = file_paths
        self.pattern = pattern
        self._is_running = True

    def stop(self):
        self._is_running = False

    def _to_letter(self, n: int, upper: bool = True) -> str:
        result = ""
        while n > 0:
            n -= 1
            result = chr((n % 26) + (ord('A') if upper else ord('a'))) + result
            n //= 26
        return result

    def _to_roman(self, n: int) -> str:
        roman_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                     (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                     (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
        result = ""
        num = n
        for value, symbol in roman_map:
            while num >= value:
                result += symbol
                num -= value
        return result

    def _to_greek(self, n: int) -> str:
        greek = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
                 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']
        if n <= len(greek):
            return greek[n - 1]
        result = ""
        while n > 0:
            n -= 1
            result = greek[n % 24] + result
            n //= 24
        return result

    def _get_next_value(self, rule: dict, index: int) -> str:
        if rule['type'] == '数字':
            return str(rule['start_num'] + index).zfill(rule['padding'])
        elif rule['type'] == '大写字母':
            return self._to_letter(rule['start_num'] + index, upper=True)
        elif rule['type'] == '小写字母':
            return self._to_letter(rule['start_num'] + index, upper=False)
        elif rule['type'] == '罗马数字':
            return self._to_roman(rule['start_num'] + index)
        elif rule['type'] == '希腊字母':
            return self._to_greek(rule['start_num'] + index)
        return ""

    def _build_name(self, index: int, ext: str) -> str:
        parts = []
        for rule in self.pattern:
            if rule['type'] == '扩展名':
                continue
            elif rule['type'] in ['数字', '大写字母', '小写字母', '罗马数字', '希腊字母']:
                parts.append(self._get_next_value(rule, index))
            else:
                parts.append(rule['text'])
        return ''.join(parts) + ext

    def run(self):
        total = len(self.file_paths)
        renamed = 0
        failed = 0

        for idx, file_path in enumerate(self.file_paths, 1):
            if not self._is_running:
                break

            dir_path = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1]
            new_name = self._build_name(idx - 1, ext)
            new_path = os.path.join(dir_path, new_name)

            if os.path.basename(file_path) == new_name:
                renamed += 1
                continue

            if os.path.exists(new_path):
                failed += 1
                continue

            try:
                os.rename(file_path, new_path)
                renamed += 1
            except:
                failed += 1

        self.finished.emit(True, f"完成！成功: {renamed}，失败: {failed}")


class RenameView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.rules = []
        self.ext_block = None
        self.worker = None
        self._is_recursive = False
        self._setup_ui()
        self._add_default_blocks()

    def _setup_ui(self):
        print("🔥 _setup_ui 被执行了")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # 命名规则
        rule_group = QGroupBox("📝 命名规则")
        rule_layout = QVBoxLayout(rule_group)
        rule_layout.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(50)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.rule_container = QWidget()
        self.rule_layout = QHBoxLayout(self.rule_container)
        self.rule_layout.setSpacing(6)
        self.rule_layout.setContentsMargins(4, 4, 4, 4)
        self.rule_layout.setAlignment(Qt.AlignLeft)
        scroll.setWidget(self.rule_container)
        rule_layout.addWidget(scroll)

        add_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.setFixedSize(70, 30)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #5e6ad2; color: white; border: none; border-radius: 6px; font-size: 13px; }
            QPushButton:hover { background: #4a56c2; }
        """)
        self.add_btn.clicked.connect(self._show_add_menu)
        add_layout.addWidget(self.add_btn)
        add_layout.addStretch()
        rule_layout.addLayout(add_layout)

        layout.addWidget(rule_group)

        # 预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(2)
        preview_layout.setContentsMargins(8, 6, 8, 6)

        self.preview_labels = []
        for i in range(3):
            label = QLabel(f"示例 {i + 1}: ")
            label.setStyleSheet("font-family: monospace; font-size: 13px; padding: 2px 6px;")
            preview_layout.addWidget(label)
            self.preview_labels.append(label)

        layout.addWidget(preview_group)

        # 拖拽区域
        file_group = QGroupBox("📁 待重命名文件")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(6)

        self.drop_label = QLabel("📂 拖拽文件或文件夹到此处")
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc; border-radius: 6px;
                padding: 12px; color: #888; background: #fafafa;
                font-size: 13px;
            }
        """)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(50)
        self.drop_label.setAcceptDrops(True)
        file_layout.addWidget(self.drop_label)

        # 递归开关 + 过滤
        toggle_row = QHBoxLayout()
        self.recursive_check = QCheckBox("包含子文件夹")
        self.recursive_check.setStyleSheet("font-size: 13px;")
        self.recursive_check.stateChanged.connect(self._on_recursive_changed)
        toggle_row.addWidget(self.recursive_check)

        toggle_row.addWidget(QLabel("  过滤:"))
        self.ext_filter = QComboBox()
        self.ext_filter.addItems(["所有文件 (*.*)", "视频 (*.mp4 *.mov *.avi)", "图片 (*.jpg *.png)", "音频 (*.mp3)"])
        self.ext_filter.setFixedWidth(160)
        toggle_row.addWidget(self.ext_filter)
        toggle_row.addStretch()
        file_layout.addLayout(toggle_row)

        self.file_count = QLabel("已选: 0 个文件")
        self.file_count.setStyleSheet("font-size: 13px; color: #555; padding: 4px;")
        file_layout.addWidget(self.file_count)

        layout.addWidget(file_group)



    def _close_window(self):
        """关闭窗口"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "正在执行重命名，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                self.window().close()
        else:
            self.window().close()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #5e6ad2; border-radius: 6px;
                    padding: 12px; color: #5e6ad2; background: #eef0ff;
                    font-size: 13px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc; border-radius: 6px;
                padding: 12px; color: #888; background: #fafafa;
                font-size: 13px;
            }
        """)

    def dropEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc; border-radius: 6px;
                padding: 12px; color: #888; background: #fafafa;
                font-size: 13px;
            }
        """)

        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                files.extend(self._get_files_from_folder(path))
            elif os.path.isfile(path):
                files.append(path)

        if files:
            self.files = list(set(self.files + files))
            self.file_count.setText(f"已选: {len(self.files)} 个文件")

    def _get_files_from_folder(self, folder_path: str) -> list:
        ext_list = self._get_ext_list()
        files = []

        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                ext = os.path.splitext(f)[1].lower()
                if not ext_list or ext in ext_list:
                    files.append(full_path)

        if self._is_recursive:
            reply = QMessageBox.question(
                self, "确认递归",
                "将扫描所有子文件夹，可能包含大量文件。\n继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                for root, dirs, dir_files in os.walk(folder_path):
                    for f in dir_files:
                        full_path = os.path.join(root, f)
                        ext = os.path.splitext(f)[1].lower()
                        if not ext_list or ext in ext_list:
                            files.append(full_path)

        return files

    def _get_ext_list(self) -> list:
        text = self.ext_filter.currentText()
        if "视频" in text:
            return ['.mp4', '.mov', '.avi', '.mkv']
        elif "图片" in text:
            return ['.jpg', '.jpeg', '.png', '.gif']
        elif "音频" in text:
            return ['.mp3', '.wav', '.flac']
        return []

    def _on_recursive_changed(self):
        self._is_recursive = self.recursive_check.isChecked()
        self.drop_label.setText(
            "📂 拖拽文件夹到此处（递归）" if self._is_recursive else "📂 拖拽文件或文件夹到此处"
        )

    def _add_default_blocks(self):
        self._add_block("固定", "既往优质_")
        config = {'type': '数字', 'start': '1', 'end': '10000', 'padding': 3}
        self._add_number_block_with_config(config)
        self.ext_block = RuleBlock("扩展名", ".mp4", removable=False)
        self.ext_block.changed.connect(self._update_preview)
        self.rule_layout.addWidget(self.ext_block)
        self.rules.append(self.ext_block)
        self._update_preview()

    def _add_block(self, block_type: str, text: str = ""):
        block = RuleBlock(block_type, text, removable=True)
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)

        ext_index = -1
        for i, rule in enumerate(self.rules):
            if rule.block_type == "扩展名":
                ext_index = i
                break

        if ext_index >= 0:
            self.rules.insert(ext_index, block)
            self.rule_layout.insertWidget(ext_index, block)
        else:
            self.rules.append(block)
            self.rule_layout.addWidget(block)

        self._update_preview()

    def _add_number_block_with_config(self, config):
        start = config.get('start', '1')
        end = config.get('end', '10000')
        display_text = f"{start} → {end}"

        block = RuleBlock("编号", display_text, removable=True)
        block.number_config = config
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)
        block.edit_requested.connect(self._edit_number_block)

        ext_index = -1
        for i, rule in enumerate(self.rules):
            if rule.block_type == "扩展名":
                ext_index = i
                break

        if ext_index >= 0:
            self.rules.insert(ext_index, block)
            self.rule_layout.insertWidget(ext_index, block)
        else:
            self.rules.append(block)
            self.rule_layout.addWidget(block)

        self._update_preview()

    def _edit_number_block(self, block):
        if not block.number_config:
            block.number_config = {'type': '数字', 'start': '1', 'end': '10000', 'padding': 3}

        dialog = NumberFormatDialog(self, block.number_config)
        if dialog.exec():
            config = dialog.get_config()
            block.number_config = config
            start = config.get('start', '1')
            end = config.get('end', '10000')
            block.set_text(f"{start} → {end}")
            block.changed.emit()
            self._update_preview()

    def _remove_block(self, block):
        if not block.removable:
            return
        self.rule_layout.removeWidget(block)
        if block in self.rules:
            self.rules.remove(block)
        block.deleteLater()
        self._update_preview()

    def _show_add_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 16px; border-radius: 4px; }
            QMenu::item:selected { background: #eef0ff; }
        """)
        menu.addAction("📝 固定文本").triggered.connect(lambda: self._add_block("固定", "新文本"))
        menu.addAction("📌 前缀").triggered.connect(lambda: self._add_block("前缀", "前缀_"))
        menu.addAction("🏷️ 后缀").triggered.connect(lambda: self._add_block("后缀", "_后缀"))
        menu.addAction("🔢 编号").triggered.connect(self._add_number_block)
        menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))

    def _add_number_block(self):
        dialog = NumberFormatDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            self._add_number_block_with_config(config)

    def _to_letter(self, n: int, upper: bool = True) -> str:
        result = ""
        while n > 0:
            n -= 1
            result = chr((n % 26) + (ord('A') if upper else ord('a'))) + result
            n //= 26
        return result

    def _to_roman(self, n: int) -> str:
        roman_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                     (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                     (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
        result = ""
        num = n
        for value, symbol in roman_map:
            while num >= value:
                result += symbol
                num -= value
        return result

    def _to_greek(self, n: int) -> str:
        greek = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
                 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']
        if n <= len(greek):
            return greek[n - 1]
        result = ""
        while n > 0:
            n -= 1
            result = greek[n % 24] + result
            n //= 24
        return result

    def _update_preview(self):
        ext = ".mp4"
        for block in self.rules:
            if block.block_type == "扩展名":
                text = block.get_text()
                ext = text if text.startswith('.') else f".{text}"
                break

        number_config = None
        for block in self.rules:
            if block.block_type == "编号":
                number_config = getattr(block, 'number_config', None)
                break

        for i in range(3):
            parts = []
            for block in self.rules:
                if block.block_type == "扩展名":
                    continue
                elif block.block_type == "编号" and number_config:
                    type_name = number_config.get('type', '数字')
                    start = number_config.get('start', '1')
                    padding = number_config.get('padding', 3)

                    if type_name == '数字':
                        parts.append(str(int(start) + i).zfill(padding))
                    elif type_name == '大写字母':
                        num = ord(start.upper()) - ord('A') + 1 + i
                        parts.append(self._to_letter(num, upper=True))
                    elif type_name == '小写字母':
                        num = ord(start.lower()) - ord('a') + 1 + i
                        parts.append(self._to_letter(num, upper=False))
                    elif type_name == '罗马数字':
                        parts.append(self._to_roman(int(start) + i))
                    elif type_name == '希腊字母':
                        parts.append(self._to_greek(int(start) + i))
                    else:
                        parts.append("001")
                elif block.block_type == "编号":
                    parts.append("001")
                else:
                    parts.append(block.get_text())

            self.preview_labels[i].setText(f"示例 {i + 1}: {''.join(parts)}{ext}")

    def _build_pattern(self) -> list:
        pattern = []
        for block in self.rules:
            if block.block_type == "扩展名":
                continue
            elif block.block_type == "编号":
                config = getattr(block, 'number_config', None)
                if config:
                    type_name = config.get('type', '数字')
                    start = config.get('start', '1')
                    if type_name == '数字':
                        start_num = int(start)
                    elif type_name in ['大写字母', '小写字母']:
                        start_num = ord(start.upper()) - ord('A') + 1 if start else 1
                    else:
                        start_num = int(start) if start.isdigit() else 1

                    pattern.append({
                        'type': type_name,
                        'start_num': start_num,
                        'padding': config.get('padding', 3),
                    })
                else:
                    pattern.append({'type': '数字', 'start_num': 1, 'padding': 3})
            else:
                pattern.append({'type': block.block_type, 'text': block.get_text()})
        return pattern

    def _execute(self):
        if not self.files:
            QMessageBox.warning(self, "提示", "请拖拽文件或文件夹！")
            return

        has_number = any(b.block_type == "编号" for b in self.rules)
        if not has_number:
            reply = QMessageBox.question(
                self, "确认",
                "规则中没有编号，所有文件将重命名为相同名称！\n继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 生成示例
        pattern = self._build_pattern()
        ext = os.path.splitext(self.files[0])[1]
        samples = []
        for i in range(3):
            parts = []
            for rule in pattern:
                if rule['type'] == '扩展名':
                    continue
                elif rule['type'] in ['数字', '大写字母', '小写字母', '罗马数字', '希腊字母']:
                    if rule['type'] == '数字':
                        parts.append(str(rule['start_num'] + i).zfill(rule['padding']))
                    elif rule['type'] == '大写字母':
                        parts.append(self._to_letter(rule['start_num'] + i, upper=True))
                    elif rule['type'] == '小写字母':
                        parts.append(self._to_letter(rule['start_num'] + i, upper=False))
                    elif rule['type'] == '罗马数字':
                        parts.append(self._to_roman(rule['start_num'] + i))
                    elif rule['type'] == '希腊字母':
                        parts.append(self._to_greek(rule['start_num'] + i))
                else:
                    parts.append(rule['text'])
            samples.append(''.join(parts) + ext)

        reply = QMessageBox.question(
            self, "确认重命名",
            f"将重命名 {len(self.files)} 个文件\n\n"
            f"示例:\n  {samples[0]}\n  {samples[1]}\n  {samples[2]}\n\n"
            f"继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.execute_btn.setEnabled(False)

        progress = QProgressDialog("正在重命名...", "取消", 0, len(self.files), self)
        progress.setWindowTitle("处理中")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        self.worker = RenameWorker(self.files.copy(), pattern)
        self.worker.progress.connect(lambda c, t, n: progress.setValue(c))
        self.worker.finished.connect(lambda s, m: self._on_finished(s, m, progress))
        self.worker.start()

    def _on_finished(self, success, msg, progress):
        progress.close()
        self.execute_btn.setEnabled(True)

        reply = QMessageBox.question(
            self, "完成", f"{msg}\n\n是否打开目标文件夹查看？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes and self.files:
            folder = os.path.dirname(self.files[0])
            os.startfile(folder)