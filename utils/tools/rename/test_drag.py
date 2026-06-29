#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QGroupBox,
    QMenu,
    QMessageBox,
    QFrame,
    QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDrag, QPainter


class RuleWidget(QFrame):
    """规则块 - 干净简洁风格"""

    def __init__(self, tag: str, text: str, color: str = "#f1f4f9", removable=True, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.text = text
        self.color = color
        self.removable = removable
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(140, 72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # ===== 上面：tag + 删除 =====
        top = QHBoxLayout()
        top.setSpacing(8)

        # tag 标签 - 自适应宽度圆角框
        tag_label = QLabel(self.tag)
        tag_label.setStyleSheet("""
            QLabel {
                background: rgba(255,255,255,0.75);
                color: #6b7280;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 12px;
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.04);
            }
        """)
        top.addWidget(tag_label)

        top.addStretch()

        # 删除按钮 - 文字 "删除"
        if self.removable:
            self.del_btn = QPushButton("删除")
            self.del_btn.setFixedSize(40, 20)
            self.del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #9ca3af;
                    border: none;
                    font-size: 11px;
                    font-weight: 400;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: #dc2626;
                }
            """)
            top.addWidget(self.del_btn)
        else:
            lock = QLabel("🔒")
            lock.setStyleSheet("font-size: 10px; color: #d1d5db;")
            top.addWidget(lock)

        layout.addLayout(top)

        # ===== 下面：输入框 =====
        self.edit = QLineEdit(self.text)
        self.edit.setAlignment(Qt.AlignCenter)
        self.edit.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 15px;
                font-weight: 500;
                color: #1f2937;
                padding: 2px 0;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
                font-weight: 400;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                border-radius: 6px;
                background: #ffffff;
                padding: 2px 4px;
            }
        """)
        self.edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.edit)

        self.update_style()

    def update_style(self, is_dragging=False):
        border = "2px solid #818cf8" if is_dragging else "1px solid #e5e7eb"
        shadow = "0 2px 8px rgba(0,0,0,0.04)" if not is_dragging else "0 4px 16px rgba(99,102,241,0.15)"
        self.setStyleSheet(f"""
            QFrame {{
                background: {self.color};
                border: {border};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: #a5b4fc;
                background: {self._hover_color()};
            }}
        """)

    def _hover_color(self):
        """悬停时稍微加深颜色"""
        if "#f1f4f9" in self.color:
            return "#e8ecf4"
        elif "#eef2ff" in self.color:
            return "#e4e8ff"
        elif "#fef3c7" in self.color:
            return "#fde8b3"
        elif "#d1fae5" in self.color:
            return "#bcf5d9"
        return "#f5f5f5"

    def on_text_changed(self, text):
        self.text = text

    def get_text(self):
        return self.edit.text()

    def get_tag(self):
        return self.tag


class DragListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(False)
        self.setSpacing(12)
        self._update_preview_callback = lambda: None

        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #e5e7eb;
                border-radius: 14px;
                background: #f8fafc;
                padding: 14px 18px;
            }
            QListWidget::item {
                background: transparent;
                padding: 0px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)

    def set_preview_update_func(self, func):
        self._update_preview_callback = func

    def startDrag(self, supportedActions):
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
        super().dropEvent(event)
        self._update_preview_callback()


class DragTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("规则块拖拽排序")
        self.setMinimumSize(820, 460)
        self.setStyleSheet("""
            QMainWindow {
                background: #ffffff;
            }
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
            QPushButton#primary {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#primary:hover {
                background: #4f46e5;
            }
            QPushButton#danger {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#danger:hover {
                background: #fecaca;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🧩 命名规则编排")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1f2937;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        info = QLabel("↔ 拖拽调整顺序 · 点击文字编辑 · 删除")
        info.setStyleSheet("color: #6b7280; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(info)

        self.rule_list = DragListWidget()
        self.rule_list.setFixedHeight(130)
        self.rule_list.set_preview_update_func(self.update_preview)
        layout.addWidget(self.rule_list)

        action_bar = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.show_add_menu)
        action_bar.addWidget(self.add_btn)

        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setObjectName("danger")
        self.clear_btn.clicked.connect(self.clear_all)
        action_bar.addWidget(self.clear_btn)

        action_bar.addStretch()
        layout.addLayout(action_bar)

        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QLabel("示例: 既往优质_001.mp4")
        self.preview.setStyleSheet("""
            QLabel {
                font-family: 'SF Mono', 'Menlo', monospace;
                font-size: 15px;
                color: #1f2937;
                background: #f8fafc;
                padding: 12px 16px;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)
        preview_layout.addWidget(self.preview)
        layout.addWidget(preview_group)

        # 默认项 - 使用更柔和的颜色
        self._add_item("固定", "既往优质_", "#f1f4f9")
        self._add_item("编号", "001", "#fef3c7")
        self._add_item("扩展名", ".mp4", "#d1fae5", removable=False)

        self.update_preview()

    def _add_item(self, tag, text, color="#f1f4f9", removable=True):
        widget = RuleWidget(tag, text, color, removable)
        widget.edit.textChanged.connect(self.update_preview)
        if hasattr(widget, 'del_btn'):
            widget.del_btn.clicked.connect(lambda: self._remove_item(widget))

        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.rule_list.addItem(item)
        self.rule_list.setItemWidget(item, widget)

    def _remove_item(self, widget):
        for i in range(self.rule_list.count()):
            item = self.rule_list.item(i)
            if self.rule_list.itemWidget(item) == widget:
                self.rule_list.takeItem(i)
                widget.deleteLater()
                self.update_preview()
                return

    def remove_selected(self):
        row = self.rule_list.currentRow()
        if row < 0:
            return
        item = self.rule_list.item(row)
        widget = self.rule_list.itemWidget(item)
        if widget and "扩展名" in widget.get_tag():
            QMessageBox.warning(self, "提示", "扩展名不能删除")
            return
        self.rule_list.takeItem(row)
        self.update_preview()

    def clear_all(self):
        for i in range(self.rule_list.count() - 1, -1, -1):
            item = self.rule_list.item(i)
            widget = self.rule_list.itemWidget(item)
            if widget and "扩展名" in widget.get_tag():
                continue
            self.rule_list.takeItem(i)
        self.update_preview()

    def show_add_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #eef2ff;
            }
        """)
        menu.addAction("📝 固定文本", lambda: self._add_item("固定", "新文本", "#f1f4f9"))
        menu.addAction("📌 前缀", lambda: self._add_item("前缀", "前缀_", "#f1f4f9"))
        menu.addAction("🏷️ 后缀", lambda: self._add_item("后缀", "_后缀", "#f1f4f9"))
        menu.addAction("🔢 编号", lambda: self._add_item("编号", "001", "#fef3c7"))
        menu.addAction("📄 原文件名", lambda: self._add_item("原文件名", "{原文件名}", "#fef3c7"))
        menu.addSeparator()
        menu.addAction("🗑️ 删除选中", self.remove_selected)
        menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))

    def update_preview(self):
        parts = []
        ext = ".mp4"

        for i in range(self.rule_list.count()):
            item = self.rule_list.item(i)
            widget = self.rule_list.itemWidget(item)
            if not widget:
                continue

            tag = widget.get_tag()
            text = widget.get_text()

            if "扩展名" in tag:
                ext = text if text.startswith('.') else f".{text}"
            else:
                parts.append(text)

        result = []
        for i in range(3):
            num = i + 1
            temp = []
            for p in parts:
                if p == "001":
                    temp.append(str(num).zfill(3))
                else:
                    temp.append(p)
            result.append("".join(temp) + ext)

        self.preview.setText("示例: " + " ，".join(result))


def main():
    app = QApplication(sys.argv)
    win = DragTestWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()