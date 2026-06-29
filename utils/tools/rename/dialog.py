# utils/tools/rename/dialog.py
"""编号格式设置弹窗 + 过滤弹窗 + 设置弹窗"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QCheckBox, QScrollArea, QWidget,
    QMessageBox
)
from PySide6.QtCore import Qt


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

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("起始值:"))
        self.start_input = QLineEdit()
        self.start_input.setFixedWidth(150)
        self.start_input.setPlaceholderText("1 或 A 或 I")
        row2.addWidget(self.start_input)
        row2.addStretch()
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("结束值:"))
        self.end_input = QLineEdit()
        self.end_input.setFixedWidth(150)
        self.end_input.setPlaceholderText("100 或 Z 或 X")
        row3.addWidget(self.end_input)
        row3.addStretch()
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("编号位数:"))
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(1, 6)
        self.padding_spin.setValue(3)
        self.padding_spin.setFixedWidth(80)
        row4.addWidget(self.padding_spin)
        row4.addStretch()
        layout.addLayout(row4)

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


class FilterDialog(QDialog):
    """文件格式过滤弹窗 - 极简稳定版"""

    def __init__(self, parent=None, current_selection=None):
        super().__init__(parent)
        self.setWindowTitle("选择文件格式")
        self.setMinimumSize(500, 400)
        self.setSizeGripEnabled(True)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QCheckBox { padding: 2px 4px; }
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
        layout.setSpacing(8)

        # 全选按钮
        self.select_all = QCheckBox("全选")
        self.select_all.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                font-size: 13px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QCheckBox:checked {
                color: #e74c3c;
                background-color: #fde8e8;
            }
            QCheckBox:!checked {
                color: #333;
                background-color: transparent;
            }
        """)
        self.select_all.clicked.connect(self._on_select_all_clicked)
        layout.addWidget(self.select_all)

        # 类别分组
        self.categories = {
            "🎬 视频": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
            "🖼️ 图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
            "🎵 音频": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "📄 文档": [".pdf", ".doc", ".docx", ".txt", ".xlsx"],
            "📦 其他": [".zip", ".rar", ".7z", ".iso"],
        }

        self.checkboxes = {}  # ext -> QCheckBox
        self.category_buttons = {}  # category -> QCheckBox

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(4)

        for category, exts in self.categories.items():
            group = QGroupBox(category)
            group_layout = QHBoxLayout(group)
            group_layout.setSpacing(6)
            group_layout.setContentsMargins(8, 4, 8, 4)

            cat_cb = QCheckBox("全选")
            cat_cb.setStyleSheet("""
                font-size: 11px;
                color: #888;
                padding: 2px 4px;
                border-radius: 3px;
            """)
            cat_cb.clicked.connect(lambda checked, e=exts: self._on_category_clicked(checked, e))
            group_layout.addWidget(cat_cb)
            self.category_buttons[category] = cat_cb

            for ext in exts:
                cb = QCheckBox(ext)
                cb.setStyleSheet("font-size: 12px;")
                cb.clicked.connect(self._on_item_clicked)
                group_layout.addWidget(cb)
                self.checkboxes[ext] = cb

            group_layout.addStretch()
            scroll_layout.addWidget(group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

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

        # 加载当前选择
        if current_selection:
            for ext in current_selection:
                if ext in self.checkboxes:
                    self.checkboxes[ext].setChecked(True)

        self._update_all()

    def _on_select_all_clicked(self):
        """全选按钮点击"""
        checked = self.select_all.isChecked()
        for cb in self.checkboxes.values():
            cb.setChecked(checked)
        self._update_all()

    def _on_category_clicked(self, checked, exts):
        """类别按钮点击"""
        for ext in exts:
            if ext in self.checkboxes:
                self.checkboxes[ext].setChecked(checked)
        self._update_all()

    def _on_item_clicked(self):
        """子项点击"""
        self._update_all()

    def _update_all(self):
        """更新所有按钮状态"""
        if not self.checkboxes:
            return

        # 计算全选状态
        all_checked = all(cb.isChecked() for cb in self.checkboxes.values())
        self.select_all.blockSignals(True)
        self.select_all.setChecked(all_checked)
        self.select_all.blockSignals(False)

        # 全选按钮样式
        if all_checked:
            self.select_all.setStyleSheet("""
                QCheckBox {
                    font-weight: 600;
                    font-size: 13px;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: #e74c3c;
                    background-color: #fde8e8;
                }
            """)
        else:
            self.select_all.setStyleSheet("""
                QCheckBox {
                    font-weight: 600;
                    font-size: 13px;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: #333;
                    background-color: transparent;
                }
            """)

        # 更新每个类别按钮
        for category, exts in self.categories.items():
            cat_checked = all(self.checkboxes[ext].isChecked() for ext in exts if ext in self.checkboxes)
            cat_cb = self.category_buttons.get(category)
            if cat_cb:
                cat_cb.blockSignals(True)
                cat_cb.setChecked(cat_checked)
                cat_cb.blockSignals(False)
                if cat_checked:
                    cat_cb.setStyleSheet("""
                        font-size: 11px;
                        color: #e74c3c;
                        font-weight: 600;
                        padding: 2px 4px;
                        border-radius: 3px;
                    """)
                else:
                    cat_cb.setStyleSheet("""
                        font-size: 11px;
                        color: #888;
                        padding: 2px 4px;
                        border-radius: 3px;
                    """)

    def get_selected(self) -> list:
        return [ext for ext, cb in self.checkboxes.items() if cb.isChecked()]


class SettingsDialog(QDialog):
    """设置弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(420, 280)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; }
            QLabel { color: #333; }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QCheckBox { padding: 4px 0; }
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
        layout.setSpacing(12)

        # 通用设置
        general_group = QGroupBox("通用")
        general_layout = QVBoxLayout(general_group)

        self.ignore_readonly = QCheckBox("忽略只读文件（选中=不修改只读文件）")
        self.ignore_readonly.setChecked(True)
        general_layout.addWidget(self.ignore_readonly)

        layout.addWidget(general_group)

        # 替换模式设置
        replace_group = QGroupBox("替换模式")
        replace_layout = QVBoxLayout(replace_group)

        # 正则表达式开关 + 问号
        regex_row = QHBoxLayout()
        self.regex_enabled = QCheckBox("开启正则表达式")
        self.regex_enabled.setChecked(False)
        regex_row.addWidget(self.regex_enabled)

        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setStyleSheet("""
            QPushButton {
                background: #5e6ad2;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #4a56c2; }
        """)
        help_btn.clicked.connect(self._show_regex_help)
        regex_row.addWidget(help_btn)
        regex_row.addStretch()
        replace_layout.addLayout(regex_row)

        # 正则示例说明
        self.regex_hint = QLabel("")
        self.regex_hint.setStyleSheet("color: #888; font-size: 12px; padding: 4px 8px; background: #f0f0f0; border-radius: 4px;")
        self.regex_hint.setVisible(False)
        replace_layout.addWidget(self.regex_hint)

        layout.addWidget(replace_group)

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

        # 连接信号
        self.regex_enabled.stateChanged.connect(self._on_regex_toggled)

    def _on_regex_toggled(self, state):
        if state == Qt.Checked:
            self.regex_hint.setVisible(True)
            self.regex_hint.setText(
                "📖 常用正则示例：\n"
                "   .* - 匹配任意字符\n"
                "   ^ - 匹配行首\n"
                "   $ - 匹配行尾\n"
                "   \\d+ - 匹配数字\n"
                "   [a-z] - 匹配小写字母\n"
                "   示例: 将 'IMG_001' 替换为 'photo_001'"
            )
        else:
            self.regex_hint.setVisible(False)

    def _show_regex_help(self):
        QMessageBox.information(
            self,
            "正则表达式帮助",
            "📖 常用正则表达式示例：\n\n"
            "• .* - 匹配任意字符\n"
            "• ^ - 匹配行首\n"
            "• $ - 匹配行尾\n"
            "• \\d+ - 匹配一个或多个数字\n"
            "• [a-z] - 匹配任意小写字母\n"
            "• [A-Z] - 匹配任意大写字母\n"
            "• (.*) - 捕获分组，用于替换\n\n"
            "💡 示例：\n"
            "   查找: IMG_(\\d+)\n"
            "   替换: photo_\\1\n"
            "   结果: IMG_001 → photo_001"
        )

    def get_settings(self):
        return {
            'ignore_readonly': self.ignore_readonly.isChecked(),
            'regex_enabled': self.regex_enabled.isChecked(),
        }
class RegexDialog(QDialog):
    """正则表达式输入弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正则表达式替换")
        self.setFixedSize(450, 250)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; }
            QLabel { color: #333; }
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                font-family: monospace;
            }
            QLineEdit:focus {
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
            QPushButton#help_btn {
                background: transparent;
                color: #5e6ad2;
                font-size: 14px;
            }
            QPushButton#help_btn:hover {
                text-decoration: underline;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 提示
        tip = QLabel("💡 正则表达式替换原文件名中的内容（不改变扩展名）")
        tip.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(tip)

        # 查找
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText(r"例如: \d+ 或 IMG_")
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)

        # 替换
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("替换为:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText(r"例如: photo_ 或 新前缀")
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)

        # 示例预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("示例: IMG_001.mp4 → IMG_001.mp4")
        self.preview_label.setStyleSheet("font-family: monospace; font-size: 13px; padding: 4px;")
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_group)

        # 常用正则帮助按钮
        help_row = QHBoxLayout()
        help_btn = QPushButton("📖 常用正则示例")
        help_btn.setObjectName("help_btn")
        help_btn.clicked.connect(self._show_help)
        help_row.addWidget(help_btn)
        help_row.addStretch()
        layout.addLayout(help_row)

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

        # 实时预览
        self.find_input.textChanged.connect(self._update_preview)
        self.replace_input.textChanged.connect(self._update_preview)

    def _update_preview(self):
        import re
        find = self.find_input.text()
        replace = self.replace_input.text()
        sample = "IMG_001.mp4"
        if find:
            try:
                result = re.sub(find, replace, sample)
                self.preview_label.setText(f"示例: {sample} → {result}")
            except:
                self.preview_label.setText("⚠️ 正则表达式语法错误")
        else:
            self.preview_label.setText(f"示例: {sample} → {sample}")

    def _show_help(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "正则表达式帮助",
            "📖 常用正则表达式示例：\n\n"
            "• .* - 匹配任意字符\n"
            "• .+ - 匹配至少一个字符\n"
            "• ^ - 匹配行首\n"
            "• $ - 匹配行尾\n"
            "• \\d+ - 匹配一个或多个数字\n"
            "• [a-z] - 匹配任意小写字母\n"
            "• [A-Z] - 匹配任意大写字母\n"
            "• (.*) - 捕获分组，用于替换\n\n"
            "💡 示例：\n"
            "   查找: IMG_(\\d+)\n"
            "   替换: photo_\\1\n"
            "   结果: IMG_001 → photo_001"
        )

    def get_find_text(self):
        return self.find_input.text().strip()

    def get_replace_text(self):
        return self.replace_input.text().strip()