# utils/tools/rename/widget.py
"""规则块组件 + 侧边面板"""

import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMenu, QSizePolicy, QWidget,
    QVBoxLayout, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QHeaderView, QToolTip, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDrag, QPainter


class RuleBlock(QFrame):
    """规则块 - 支持拖拽的卡片样式"""
    changed = Signal()
    remove_requested = Signal(object)
    edit_requested = Signal(object)

    COLORS = {
        "固定": "#f1f4f9",
        "前缀": "#f1f4f9",
        "后缀": "#f1f4f9",
        "编号": "#fef3c7",
        "原文件名": "#eef2ff",
        "扩展名": "#d1fae5",
    }

    def __init__(self, block_type="固定", default_text="", removable=True, parent=None):
        super().__init__(parent)
        self.block_type = block_type
        self.is_editing = False
        self.removable = removable
        self.number_config = None
        self._is_dragging = False
        self._setup_ui(default_text)
        self.update_style()
        self.setAcceptDrops(True)

    def _setup_ui(self, default_text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        # 类型标签
        self.type_label = QLabel(self.block_type)
        self.type_label.setStyleSheet("""
            QLabel {
                background: rgba(255,255,255,0.75);
                color: #6b7280;
                font-size: 10px;
                font-weight: 500;
                padding: 2px 10px;
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.04);
            }
        """)
        layout.addWidget(self.type_label)

        # 内容
        self.display_label = QLabel(default_text or "点击编辑")
        self.display_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #1f2937;
                padding: 2px 6px;
                border: none;
                background: transparent;
            }
        """)
        self.display_label.mousePressEvent = self._start_edit
        layout.addWidget(self.display_label)

        self.edit_input = QLineEdit(default_text)
        self.edit_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #6366f1;
                border-radius: 6px;
                background: white;
                font-size: 13px;
                font-weight: 500;
                color: #1f2937;
                padding: 2px 6px;
            }
            QLineEdit:focus { outline: none; }
        """)
        self.edit_input.setVisible(False)
        self.edit_input.returnPressed.connect(self._finish_edit)
        self.edit_input.editingFinished.connect(self._finish_edit)
        layout.addWidget(self.edit_input)

        # 操作按钮
        if self.block_type == "编号":
            self.menu_btn = QPushButton("⚙")
            self.menu_btn.setFixedSize(24, 24)
            self.menu_btn.setStyleSheet("""
                QPushButton {
                    background: #6366f1;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 11px;
                }
                QPushButton:hover { background: #4f46e5; }
            """)
            self.menu_btn.clicked.connect(self._show_menu)
            layout.addWidget(self.menu_btn)
        elif self.block_type == "原文件名":
            lock_label = QLabel("🔒")
            lock_label.setStyleSheet("font-size: 10px; color: #9ca3af;")
            layout.addWidget(lock_label)
        elif not self.removable:
            lock_label = QLabel("🔒")
            lock_label.setStyleSheet("font-size: 10px; color: #9ca3af;")
            layout.addWidget(lock_label)
        else:
            self.remove_btn = QPushButton("✕")
            self.remove_btn.setFixedSize(22, 22)
            self.remove_btn.setStyleSheet("""
                QPushButton {
                    background: #e5e7eb;
                    color: #6b7280;
                    border: none;
                    border-radius: 11px;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #ef4444;
                    color: white;
                }
            """)
            self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
            layout.addWidget(self.remove_btn)

        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def _get_color(self):
        return self.COLORS.get(self.block_type, "#f1f4f9")

    def _hover_color(self):
        colors = {
            "#f1f4f9": "#e8ecf4",
            "#eef2ff": "#e4e8ff",
            "#fef3c7": "#fde8b3",
            "#d1fae5": "#bcf5d9",
        }
        return colors.get(self._get_color(), "#f5f5f5")

    def update_style(self, is_dragging=False):
        self._is_dragging = is_dragging
        color = self._get_color()
        border = "2px solid #818cf8" if is_dragging else "1px solid #e5e7eb"
        self.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border: {border};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: #a5b4fc;
                background: {self._hover_color()};
            }}
        """)

    def _start_edit(self, event):
        if self.block_type in ["扩展名", "原文件名"]:
            if self.block_type == "原文件名":
                QToolTip.showText(event.globalPos(), "原文件名块不可编辑，请使用替换模式修改")
            return
        self.is_editing = True
        self.display_label.setVisible(False)
        self.edit_input.setVisible(True)
        self.edit_input.setText(self.display_label.text())
        self.edit_input.setFocus()
        self.edit_input.selectAll()

    def _show_menu(self):
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
        edit_action = menu.addAction("✎ 编辑编号")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self))
        menu.addSeparator()
        delete_action = menu.addAction("✕ 删除")
        delete_action.triggered.connect(lambda: self.remove_requested.emit(self))
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())
        menu.exec(pos)

    def _finish_edit(self):
        self.is_editing = False
        text = self.edit_input.text().strip()
        if not text:
            text = "点击编辑"
        self.display_label.setText(text)
        self.edit_input.setVisible(False)
        self.display_label.setVisible(True)
        self.changed.emit()

    def get_text(self) -> str:
        if self.is_editing:
            return self.edit_input.text().strip()
        return self.display_label.text()

    def set_text(self, text: str):
        self.display_label.setText(text)
        self.edit_input.setText(text)
        self.changed.emit()

    def get_display_text(self) -> str:
        return self.display_label.text()


class DragRuleList(QListWidget):
    """可拖拽排序的规则列表 - 完全使用 test_drag.py 的逻辑"""

    rules_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(False)
        self.setSpacing(8)
        self.setFocusPolicy(Qt.NoFocus)

        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #e5e7eb;
                border-radius: 12px;
                background: #f8fafc;
                padding: 10px 14px;
                min-height: 60px;
            }
            QListWidget::item {
                background: transparent;
                padding: 0px;
                outline: none;
                border: none;
            }
            QListWidget::item:selected {
                background: transparent;
                outline: none;
                border: none;
            }
            QListWidget::item:selected:!active {
                background: transparent;
                outline: none;
                border: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
            QListWidget::item:selected:focus {
                background: transparent;
                outline: none;
                border: none;
            }
        """)

    def startDrag(self, supportedActions):
        """完全照抄 test_drag.py"""
        item = self.currentItem()
        if not item:
            return

        widget = self.itemWidget(item)
        if widget and hasattr(widget, 'update_style'):
            widget.update_style(is_dragging=True)

        mimeData = self.model().mimeData(self.selectedIndexes())
        drag = QDrag(self)
        drag.setMimeData(mimeData)

        if widget:
            pix = widget.grab()
            painter = QPainter(pix)
            painter.setOpacity(0.75)
            painter.fillRect(pix.rect(), Qt.white)
            painter.end()
            drag.setPixmap(pix)
            drag.setHotSpot(pix.rect().center())

        drag.exec(Qt.MoveAction)

        if widget and hasattr(widget, 'update_style'):
            widget.update_style(is_dragging=False)

    def dropEvent(self, event):
        """完全照抄 test_drag.py"""
        super().dropEvent(event)
        self.rules_changed.emit()

    def add_rule_block(self, block: RuleBlock):
        """添加规则块，扩展名永远在最后"""
        if block.block_type == "扩展名":
            # 先移除已有的扩展名
            existing = self.get_ext_block()
            if existing:
                self.remove_rule_block(existing)
            # 添加到末尾
            item = QListWidgetItem()
            item.setSizeHint(block.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, block)
        else:
            # 插入到扩展名前面
            ext_block = self.get_ext_block()
            if ext_block:
                ext_index = -1
                for i in range(self.count()):
                    item = self.item(i)
                    widget = self.itemWidget(item)
                    if widget and widget.block_type == "扩展名":
                        ext_index = i
                        break

                if ext_index != -1:
                    item = QListWidgetItem()
                    item.setSizeHint(block.sizeHint())
                    self.insertItem(ext_index, item)
                    self.setItemWidget(item, block)
                else:
                    item = QListWidgetItem()
                    item.setSizeHint(block.sizeHint())
                    self.addItem(item)
                    self.setItemWidget(item, block)
            else:
                item = QListWidgetItem()
                item.setSizeHint(block.sizeHint())
                self.addItem(item)
                self.setItemWidget(item, block)

        if hasattr(block, 'changed'):
            block.changed.connect(self.rules_changed.emit)
        self.rules_changed.emit()

    def insert_rule_block(self, index: int, block: RuleBlock):
        """在指定位置插入规则块，但扩展名永远在最后"""
        if block.block_type == "扩展名":
            self.add_rule_block(block)
            return

        ext_block = self.get_ext_block()
        if ext_block:
            ext_index = -1
            for i in range(self.count()):
                item = self.item(i)
                widget = self.itemWidget(item)
                if widget and widget.block_type == "扩展名":
                    ext_index = i
                    break

            if ext_index != -1 and index >= ext_index:
                index = ext_index

        item = QListWidgetItem()
        item.setSizeHint(block.sizeHint())
        self.insertItem(index, item)
        self.setItemWidget(item, block)
        if hasattr(block, 'changed'):
            block.changed.connect(self.rules_changed.emit)
        self.rules_changed.emit()

    def get_rule_blocks(self) -> list:
        """获取所有规则块"""
        blocks = []
        for i in range(self.count()):
            item = self.item(i)
            block = self.itemWidget(item)
            if block:
                blocks.append(block)
        return blocks

    def remove_rule_block(self, block: RuleBlock):
        """移除指定的规则块"""
        if block.block_type == "扩展名":
            return

        for i in range(self.count()):
            item = self.item(i)
            if self.itemWidget(item) == block:
                self.takeItem(i)
                block.deleteLater()
                self.rules_changed.emit()
                return

    def clear_all(self):
        """清空所有规则块（保留扩展名）"""
        for i in range(self.count() - 1, -1, -1):
            item = self.item(i)
            block = self.itemWidget(item)
            if block and block.block_type == "扩展名":
                continue
            self.takeItem(i)
            if block:
                block.deleteLater()
        self.rules_changed.emit()

    def get_ext_block(self) -> RuleBlock:
        """获取扩展名块"""
        for i in range(self.count()):
            item = self.item(i)
            block = self.itemWidget(item)
            if block and block.block_type == "扩展名":
                return block
        return None


# ===== FileSidePanel 保持不变 =====

class FileSidePanel(QWidget):
    """文件列表侧边面板"""

    file_removed = Signal(str)
    folder_removed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { padding: 4px 12px; }
        """)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setIndentation(12)
        self.file_tree.setMinimumHeight(200)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.file_tree.setColumnCount(1)
        self.file_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tab_widget.addTab(self.file_tree, "📋 当前文件")

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderHidden(True)
        self.history_tree.setIndentation(10)
        self.history_tree.setStyleSheet("color: #888;")
        empty_item = QTreeWidgetItem(["暂无历史记录"])
        self.history_tree.addTopLevelItem(empty_item)
        self.tab_widget.addTab(self.history_tree, "🕐 最近任务")

        layout.addWidget(self.tab_widget)

        self.clear_btn = QPushButton("🗑️ 清空全部")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover { background: #fecaca; }
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(self.clear_btn)

        self.count_label = QLabel("共 0 个项目")
        self.count_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(self.count_label)

    def _get_icon(self, path: str) -> str:
        if os.path.isdir(path):
            return "📁"
        ext = os.path.splitext(path)[1].lower()
        icon_map = {
            '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.pdf': '📄', '.doc': '📄', '.docx': '📄', '.txt': '📄',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
        }
        return icon_map.get(ext, '📄')

    def _get_display_name(self, path: str) -> str:
        name = os.path.basename(path)
        if not name:
            name = path
        if len(name) > 30:
            return name[:27] + "..."
        return name

    def _show_context_menu(self, pos):
        item = self.file_tree.itemAt(pos)
        if not item:
            return
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
        remove_action = menu.addAction("🗑️ 移除")
        remove_action.triggered.connect(lambda: self.remove_item(item))
        menu.exec(self.file_tree.mapToGlobal(pos))

    def add_items(self, paths: list):
        existing_paths = set()
        for i in range(self.file_tree.topLevelItemCount()):
            existing_paths.add(self.file_tree.topLevelItem(i).data(0, Qt.UserRole))

        for p in paths:
            if p in existing_paths:
                continue
            icon = self._get_icon(p)
            display_name = self._get_display_name(p)
            full_name = os.path.basename(p) or p
            item = QTreeWidgetItem([f"{icon}  {display_name}"])
            item.setData(0, Qt.UserRole, p)
            item.setToolTip(0, full_name)
            self.file_tree.addTopLevelItem(item)
            existing_paths.add(p)

        self._update_count()

    def add_files(self, files: list):
        self.add_items(files)

    def remove_item(self, item):
        path = item.data(0, Qt.UserRole)
        self.file_tree.takeTopLevelItem(self.file_tree.indexOfTopLevelItem(item))
        if os.path.isdir(path):
            self.folder_removed.emit(path)
        else:
            self.file_removed.emit(path)
        self._update_count()

    def remove_item_by_path(self, path: str):
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == path:
                self.file_tree.takeTopLevelItem(i)
                self._update_count()
                return

    def clear_all(self):
        self.file_tree.clear()
        self._update_count()

    def get_all_items(self) -> list:
        items = []
        for i in range(self.file_tree.topLevelItemCount()):
            items.append(self.file_tree.topLevelItem(i).data(0, Qt.UserRole))
        return items

    def _update_count(self):
        count = self.file_tree.topLevelItemCount()
        self.count_label.setText(f"共 {count} 个项目")