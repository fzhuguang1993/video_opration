# utils/tools/rename/view.py
"""批量重命名工具视图 - RenameView"""

import os
import platform
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QCheckBox,
    QMessageBox, QProgressDialog,
    QFileDialog, QSplitter, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt

from .widget import RuleBlock, FileSidePanel, DragRuleList
from .worker import RenameWorker
from .dialog import NumberFormatDialog, FilterDialog, SettingsDialog, RegexDialog


class RenameView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.worker = None
        self._is_recursive = False
        self._selected_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        self._ignore_readonly = True
        self._regex_enabled = False
        self._regex_find = ""
        self._regex_replace = ""
        self._setup_ui()
        self._add_default_blocks()

        # 设置整体宽度
        self.setMinimumWidth(900)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        # ===== 命名规则 =====
        rule_group = QGroupBox("📝 命名规则")
        rule_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
                color: #1f2937;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        rule_layout = QVBoxLayout(rule_group)
        rule_layout.setSpacing(6)

        # 使用 DragRuleList
        self.rule_list = DragRuleList()
        self.rule_list.setFixedHeight(70)
        self.rule_list.rules_changed.connect(self._update_preview)
        rule_layout.addWidget(self.rule_list)

        # 按钮和上面拉开间距
        rule_layout.addSpacing(10)

        # ===== 按钮行 =====
        add_layout = QHBoxLayout()
        add_layout.setSpacing(6)

        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedSize(60, 28)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        self.add_btn.clicked.connect(self._show_add_menu)
        add_layout.addWidget(self.add_btn)

        self.replace_mode_btn = QPushButton("普通模式")
        self.replace_mode_btn.setFixedSize(80, 28)
        self.replace_mode_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        self.replace_mode_btn.clicked.connect(self._toggle_replace_mode)
        add_layout.addWidget(self.replace_mode_btn)

        self.settings_btn = QPushButton("🔧")
        self.settings_btn.setFixedSize(44, 44)
        self.settings_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #374151;
                border: none;
                font-size: 20px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #f3f4f6;
                border-radius: 6px;
            }
        """)
        self.settings_btn.clicked.connect(self._show_settings)
        add_layout.addWidget(self.settings_btn)

        add_layout.addStretch()
        rule_layout.addLayout(add_layout)

        left_layout.addWidget(rule_group)

        # ===== 预览 =====
        preview_group = QGroupBox("预览")
        preview_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
                color: #1f2937;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(2)
        preview_layout.setContentsMargins(8, 6, 8, 6)

        self.preview_labels = []
        for i in range(3):
            label = QLabel(f"示例 {i + 1}: ")
            label.setStyleSheet("""
                font-family: 'SF Mono', 'Menlo', monospace;
                font-size: 13px;
                color: #1f2937;
                padding: 3px 8px;
                background: #f8fafc;
                border-radius: 4px;
            """)
            preview_layout.addWidget(label)
            self.preview_labels.append(label)

        left_layout.addWidget(preview_group)

        # ===== 文件区域 =====
        file_group = QGroupBox("📁 待重命名文件")
        file_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
                color: #1f2937;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(6)

        self.drop_label = QLabel("📂 拖拽文件或文件夹到此处")
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 10px;
                padding: 12px;
                color: #6b7280;
                background: #fafafa;
                font-size: 13px;
            }
        """)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(44)
        self.drop_label.setAcceptDrops(True)
        file_layout.addWidget(self.drop_label)

        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)

        self.recursive_check = QCheckBox("包含子文件夹")
        self.recursive_check.setStyleSheet("font-size: 12px; color: #374151;")
        self.recursive_check.stateChanged.connect(self._on_recursive_changed)
        toggle_row.addWidget(self.recursive_check)

        toggle_row.addWidget(QLabel("过滤:"))
        self.filter_btn = QPushButton("选择格式")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        self.filter_btn.clicked.connect(self._show_filter_dialog)
        toggle_row.addWidget(self.filter_btn)

        self.filter_label = QLabel("已选: 4 种格式")
        self.filter_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        toggle_row.addWidget(self.filter_label)

        toggle_row.addStretch()
        file_layout.addLayout(toggle_row)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(6)

        self.select_folder_btn = QPushButton("📁 选择文件夹")
        self.select_folder_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                color: #374151;
            }
            QPushButton:hover { background: #e5e7eb; }
        """)
        self.select_folder_btn.clicked.connect(self._select_folder)
        folder_row.addWidget(self.select_folder_btn)

        self.select_file_btn = QPushButton("📄 选择文件")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                color: #374151;
            }
            QPushButton:hover { background: #e5e7eb; }
        """)
        self.select_file_btn.clicked.connect(self._select_files)
        folder_row.addWidget(self.select_file_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                color: #dc2626;
            }
            QPushButton:hover { background: #fecaca; }
        """)
        self.clear_btn.clicked.connect(self._clear_all)
        folder_row.addStretch()
        file_layout.addLayout(folder_row)

        left_layout.addWidget(file_group)

        # ===== 按钮 =====
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.execute_btn = QPushButton("▶ 执行")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #4f46e5; }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        self.execute_btn.clicked.connect(self._execute)
        btn_layout.addWidget(self.execute_btn)

        self.close_btn = QPushButton("✕ 关闭")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background: #fecaca; }
        """)
        self.close_btn.clicked.connect(self._close_window)
        btn_layout.addWidget(self.close_btn)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        left_widget.setLayout(left_layout)

        # ===== 侧边面板 =====
        self.side_panel = FileSidePanel(self)
        self.side_panel.file_removed.connect(self._on_file_removed)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.side_panel)
        splitter.setSizes([700, 280])

        main_layout.addWidget(splitter)
        self.setAcceptDrops(True)

    # ===== 规则管理 =====

    def _add_default_blocks(self):
        """添加默认规则块"""
        # 固定文本
        block = RuleBlock("固定", "既往优质_")
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)
        self.rule_list.add_rule_block(block)

        # 编号
        config = {'type': '数字', 'start': '1', 'end': '10000', 'padding': 3}
        block = RuleBlock("编号", "1 → 10000")
        block.number_config = config
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)
        block.edit_requested.connect(self._edit_number_block)
        self.rule_list.add_rule_block(block)

        self._update_preview()

    def _show_add_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #eef2ff;
            }
        """)
        menu.addAction("📝 固定文本").triggered.connect(lambda: self._add_block("固定", "新文本"))
        menu.addAction("📌 前缀").triggered.connect(lambda: self._add_block("前缀", "前缀_"))
        menu.addAction("🏷️ 后缀").triggered.connect(lambda: self._add_block("后缀", "_后缀"))
        menu.addAction("🔢 编号").triggered.connect(self._add_number_block)
        menu.addAction("📄 原文件名").triggered.connect(lambda: self._add_block("原文件名", "{原文件名}"))
        menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))

    def _add_block(self, block_type: str, text: str = ""):
        """添加规则块"""
        block = RuleBlock(block_type, text, removable=True)
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)

        # 在扩展名之前插入
        ext_block = self.rule_list.get_ext_block()
        if ext_block:
            ext_index = self.rule_list.indexFromItem(
                self.rule_list.item(self.rule_list.count() - 1)
            ).row()
            self.rule_list.insert_rule_block(ext_index, block)
        else:
            self.rule_list.add_rule_block(block)

        self._update_preview()

    def _add_number_block(self):
        dialog = NumberFormatDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            self._add_number_block_with_config(config)

    def _add_number_block_with_config(self, config):
        start = config.get('start', '1')
        end = config.get('end', '10000')
        display_text = f"{start} → {end}"

        block = RuleBlock("编号", display_text, removable=True)
        block.number_config = config
        block.changed.connect(self._update_preview)
        block.remove_requested.connect(self._remove_block)
        block.edit_requested.connect(self._edit_number_block)

        ext_block = self.rule_list.get_ext_block()
        if ext_block:
            ext_index = self.rule_list.indexFromItem(
                self.rule_list.item(self.rule_list.count() - 1)
            ).row()
            self.rule_list.insert_rule_block(ext_index, block)
        else:
            self.rule_list.add_rule_block(block)

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
            self._update_preview()

    def _remove_block(self, block):
        if not block.removable:
            return
        self.rule_list.remove_rule_block(block)
        self._update_preview()

    # ===== 替换模式 =====

    def _toggle_replace_mode(self):
        """切换替换模式"""
        if "普通" in self.replace_mode_btn.text():
            dialog = RegexDialog(self)
            if dialog.exec():
                find_text = dialog.get_find_text()
                replace_text = dialog.get_replace_text()
                if find_text:
                    self.replace_mode_btn.setText("正则模式")
                    self.replace_mode_btn.setStyleSheet("""
                        QPushButton {
                            background: #dc2626;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: 500;
                        }
                        QPushButton:hover { background: #b91c1c; }
                    """)
                    self._regex_find = find_text
                    self._regex_replace = replace_text
                    QMessageBox.information(self, "正则模式",
                                            f"已启用正则模式\n\n查找: {find_text}\n替换: {replace_text}")
                else:
                    QMessageBox.warning(self, "提示", "查找内容不能为空")
            else:
                return
        else:
            self.replace_mode_btn.setText("普通模式")
            self.replace_mode_btn.setStyleSheet("""
                QPushButton {
                    background: #6b7280;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover { background: #4b5563; }
            """)
            self._regex_find = ""
            self._regex_replace = ""

    def _show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self._ignore_readonly = settings.get('ignore_readonly', True)
            self._regex_enabled = settings.get('regex_enabled', False)
            if self._regex_enabled:
                self.replace_mode_btn.setText("正则模式")
                self.replace_mode_btn.setStyleSheet("""
                    QPushButton {
                        background: #dc2626;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover { background: #b91c1c; }
                """)
            else:
                self.replace_mode_btn.setText("普通模式")
                self.replace_mode_btn.setStyleSheet("""
                    QPushButton {
                        background: #6b7280;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover { background: #4b5563; }
                """)

    # ===== 文件管理 =====

    def _show_filter_dialog(self):
        dialog = FilterDialog(self, self._selected_extensions)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                self._selected_extensions = selected
                self.filter_label.setText(f"已选: {len(selected)} 种格式")
            else:
                QMessageBox.warning(self, "提示", "至少选择一种格式！")

    def _get_ext_list(self) -> list:
        return self._selected_extensions

    def _select_files(self):
        ext_filter = " ".join([f"*{ext}" for ext in self._selected_extensions])
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            f"文件 ({ext_filter})"
        )
        if paths:
            self._add_files(paths)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            files = self._get_files_from_folder(folder)
            if files:
                for f in files:
                    if f not in self.files:
                        self.files.append(f)
                # ✅ 只在侧边栏显示文件夹，不加入 self.files
                self.side_panel.add_items([folder])
                self._update_file_count()
            else:
                QMessageBox.information(self, "提示",
                                        f"文件夹中没有符合条件的文件\n\n当前过滤格式: {', '.join(self._selected_extensions)}")

    def _add_files(self, file_paths: list):
        new_items = []
        for f in file_paths:
            if f not in self.files:
                self.files.append(f)
                new_items.append(f)
        if new_items:
            self.side_panel.add_items(new_items)
            self._update_file_count()

    def _on_file_removed(self, file_path: str):
        if file_path in self.files:
            self.files.remove(file_path)
            self._update_file_count()

    def _clear_all(self):
        self.files = []
        self.side_panel.clear_all()
        self._update_file_count()

    def _update_file_count(self):
        self.side_panel._update_count()

    # ===== 文件夹读取 =====

    def _get_files_from_folder(self, folder_path: str) -> list:
        """获取文件夹内所有符合条件的文件"""
        ext_list = self._get_ext_list()
        files = []

        try:
            if self._is_recursive:
                # 递归遍历所有子文件夹
                for root, dirs, filenames in os.walk(folder_path):
                    for f in filenames:
                        full_path = os.path.join(root, f)
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ext_list:
                            files.append(full_path)
            else:
                # 只遍历当前文件夹
                for f in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, f)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ext_list:
                            files.append(full_path)
        except Exception as e:
            print(f"读取文件夹失败: {e}")

        return files

    # ===== 拖拽 =====

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #6366f1;
                    border-radius: 10px;
                    padding: 12px;
                    color: #6366f1;
                    background: #eef2ff;
                    font-size: 13px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 10px;
                padding: 12px;
                color: #6b7280;
                background: #fafafa;
                font-size: 13px;
            }
        """)

    def dropEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #d1d5db;
                border-radius: 10px;
                padding: 12px;
                color: #6b7280;
                background: #fafafa;
                font-size: 13px;
            }
        """)

        paths = []
        folders = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                folders.append(path)
            elif os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in self._selected_extensions:
                    paths.append(path)

        # 处理文件夹：读取文件夹内的文件
        all_files = []
        if folders:
            for folder in folders:
                folder_files = self._get_files_from_folder(folder)
                all_files.extend(folder_files)
            # ✅ 只在侧边栏显示文件夹，不加入 self.files
            self.side_panel.add_items(folders)

        # 处理单个文件
        if paths:
            for p in paths:
                if p not in self.files:
                    self.files.append(p)
            self.side_panel.add_items(paths)
            all_files.extend(paths)

        # ✅ 只添加文件，不添加文件夹本身
        for f in all_files:
            if f not in self.files:
                self.files.append(f)

        # 如果只有文件夹但没有符合条件的文件，提示用户
        if folders and not all_files and not paths:
            QMessageBox.information(self, "提示",
                                    f"文件夹中没有符合条件的文件\n\n当前过滤格式: {', '.join(self._selected_extensions)}")

        self._update_file_count()

    def _on_recursive_changed(self):
        self._is_recursive = self.recursive_check.isChecked()
        self.drop_label.setText(
            "📂 拖拽文件夹到此处（递归）" if self._is_recursive else "📂 拖拽文件或文件夹到此处"
        )

    # ===== 预览 =====

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
        blocks = self.rule_list.get_rule_blocks()

        # 扩展名固定为 .mp4
        ext = ".mp4"

        # 获取编号配置
        number_config = None
        for block in blocks:
            if block.block_type == "编号":
                number_config = getattr(block, 'number_config', None)
                break

        for i in range(3):
            parts = []
            for block in blocks:
                if block.block_type == "编号" and number_config:
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
        blocks = self.rule_list.get_rule_blocks()

        for block in blocks:
            if block.block_type == "编号":
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

    # ===== 执行 =====

    def _execute(self):
        if not self.files:
            QMessageBox.warning(self, "提示", "请拖拽文件或文件夹！")
            return

        blocks = self.rule_list.get_rule_blocks()
        has_number = any(b.block_type == "编号" for b in blocks)
        if not has_number:
            reply = QMessageBox.question(
                self, "确认",
                "规则中没有编号，所有文件将重命名为相同名称！\n继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        pattern = self._build_pattern()
        ext = os.path.splitext(self.files[0])[1]
        samples = []
        for i in range(3):
            parts = []
            for rule in pattern:
                if rule['type'] in ['数字', '大写字母', '小写字母', '罗马数字', '希腊字母']:
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

        self.worker = RenameWorker(self.files.copy(), pattern, self._regex_enabled)
        self.worker.progress.connect(lambda c, t, n: progress.setValue(c))
        self.worker.finished.connect(lambda s, m, data: self._on_finished(s, m, data, progress))
        self.worker.start()

    def _on_finished(self, success, msg, result_data, progress):
        """重命名完成回调"""
        progress.close()
        self.execute_btn.setEnabled(True)

        # 保存文件夹路径（在清空前）
        folder_path = ""
        if self.files:
            folder_path = os.path.dirname(self.files[0])

        # 保存历史记录到本地
        if success and result_data:
            try:
                from .history_manager import HistoryManager
                manager = HistoryManager()

                # 构建批次数据
                files_info = []
                for r in result_data.get("results", []):
                    files_info.append({
                        "old_path": r.get("old_path", ""),
                        "new_path": r.get("new_path", ""),
                        "old_name": r.get("old_name", ""),
                        "new_name": r.get("new_name", ""),
                        "status": r.get("status", "unknown"),
                        "reason": r.get("reason", "")
                    })

                pattern = self._build_pattern()

                batch_data = {
                    "user": "当前用户",
                    "pattern": pattern,
                    "total": result_data.get("total", 0),
                    "success": result_data.get("renamed", 0),
                    "failed": result_data.get("failed", 0),
                    "files": files_info
                }

                batch_id = manager.save_batch(batch_data)
                print(f"✅ 历史记录已保存: {batch_id}")

                # 刷新历史列表
                self.side_panel.load_history()

            except Exception as e:
                print(f"❌ 保存历史记录失败: {e}")
                import traceback
                traceback.print_exc()

        # 清空文件列表
        self.files = []
        self.side_panel.clear_all()
        self._update_file_count()

        # 提示用户并询问是否打开文件夹
        reply = QMessageBox.question(
            self, "完成", f"{msg}\n\n是否打开目标文件夹查看？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes and folder_path:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])

    # ===== 关闭 =====

    def _close_window(self):
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

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "正在执行重命名，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()