#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配色调试工具 - 验证飞书风格配色是否生效
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSlider, QProgressBar,
    QTableWidget, QTableWidgetItem, QGroupBox, QCheckBox, QTextEdit,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.config import get_config


class StyleDebugger(QMainWindow):
    """配色调试窗口"""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.setWindowTitle("🎨 飞书风格配色调试")
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("🎨 飞书风格配色调试面板")
        title.setObjectName("page_title")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 状态信息
        info = QLabel("检查以下组件是否正确应用了飞书风格配色 | 主色: #3370ff")
        info.setObjectName("page_subtitle")
        info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info)

        # 环境信息
        from core.config import ENV
        env_label = QLabel(f"🌍 当前环境: {ENV}  |  缓存: {'启用' if ENV == 'production' else '禁用'}")
        env_label.setAlignment(Qt.AlignCenter)
        env_label.setStyleSheet("color: #86909c; font-size: 12px;")
        main_layout.addWidget(env_label)

        # ===== 布局 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # 1. 按钮测试
        scroll_layout.addWidget(self._create_button_section())

        # 2. 输入组件测试
        scroll_layout.addWidget(self._create_input_section())

        # 3. 滑块和进度条
        scroll_layout.addWidget(self._create_slider_section())

        # 4. 表格测试
        scroll_layout.addWidget(self._create_table_section())

        # 5. 复选框
        scroll_layout.addWidget(self._create_checkbox_section())

        # 6. 颜色标记说明
        scroll_layout.addWidget(self._create_color_legend())

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _create_button_section(self) -> QGroupBox:
        group = QGroupBox("🔘 按钮配色")
        layout = QHBoxLayout()
        layout.setSpacing(8)

        layout.addWidget(self._create_btn("普通按钮", ""))
        layout.addWidget(self._create_btn("主要按钮", "primary_btn"))
        layout.addWidget(self._create_btn("成功按钮", "success_btn"))
        layout.addWidget(self._create_btn("危险按钮", "danger_btn"))
        layout.addWidget(self._create_btn("幽灵按钮", "ghost_btn"))
        layout.addWidget(self._create_btn("禁用状态", "", enabled=False))

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_btn(self, text: str, obj_name: str = "", enabled: bool = True) -> QPushButton:
        btn = QPushButton(text)
        if obj_name:
            btn.setObjectName(obj_name)
        btn.setEnabled(enabled)
        btn.setFixedHeight(32)
        return btn

    def _create_input_section(self) -> QGroupBox:
        group = QGroupBox("📝 输入组件配色")
        layout = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel("普通输入框:"))
        edit = QLineEdit()
        edit.setPlaceholderText("输入文本...")
        left.addWidget(edit)

        left.addWidget(QLabel("禁用输入框:"))
        disabled_edit = QLineEdit()
        disabled_edit.setPlaceholderText("禁用状态")
        disabled_edit.setEnabled(False)
        left.addWidget(disabled_edit)

        right = QVBoxLayout()
        right.addWidget(QLabel("下拉选择框:"))
        combo = QComboBox()
        combo.addItems(["选项一", "选项二", "选项三"])
        right.addWidget(combo)

        right.addWidget(QLabel("禁用下拉框:"))
        disabled_combo = QComboBox()
        disabled_combo.addItems(["禁用选项一", "禁用选项二"])
        disabled_combo.setEnabled(False)
        right.addWidget(disabled_combo)

        layout.addLayout(left)
        layout.addLayout(right)
        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_slider_section(self) -> QGroupBox:
        group = QGroupBox("🎚️ 滑块 & 进度条配色")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("滑块:"))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(65)
        layout.addWidget(slider)

        layout.addWidget(QLabel("进度条:"))
        progress = QProgressBar()
        progress.setValue(75)
        progress.setMinimumHeight(12)
        layout.addWidget(progress)

        group.setLayout(layout)
        return group

    def _create_table_section(self) -> QGroupBox:
        group = QGroupBox("📊 表格配色")
        layout = QVBoxLayout()

        table = QTableWidget(4, 4)
        table.setHorizontalHeaderLabels(["名称", "状态", "大小", "日期"])
        data = [
            ["视频_001.mp4", "✅ 完成", "245 MB", "2024-01-15"],
            ["视频_002.mp4", "⏳ 处理中", "189 MB", "2024-01-16"],
            ["视频_003.mp4", "❌ 失败", "312 MB", "2024-01-17"],
            ["视频_004.mp4", "✅ 完成", "178 MB", "2024-01-18"],
        ]
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                table.setItem(row, col, item)

        table.setAlternatingRowColors(True)
        table.setMinimumHeight(120)
        layout.addWidget(table)

        group.setLayout(layout)
        return group

    def _create_checkbox_section(self) -> QGroupBox:
        group = QGroupBox("☑️ 复选框配色")
        layout = QHBoxLayout()

        cb1 = QCheckBox("普通复选框")
        cb2 = QCheckBox("选中状态")
        cb2.setChecked(True)
        cb3 = QCheckBox("禁用复选框")
        cb3.setEnabled(False)

        layout.addWidget(cb1)
        layout.addWidget(cb2)
        layout.addWidget(cb3)
        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_color_legend(self) -> QGroupBox:
        group = QGroupBox("🎨 飞书配色色板")
        layout = QHBoxLayout()

        colors = [
            ("#3370ff", "主色"),
            ("#4e89ff", "主色悬停"),
            ("#00b42a", "成功"),
            ("#f53f3f", "危险"),
            ("#1d2129", "文字主"),
            ("#4e5969", "文字次"),
            ("#86909c", "文字灰"),
            ("#e5e6eb", "边框"),
            ("#f5f6f8", "背景"),
            ("#e8f0fe", "选中"),
            ("#f2f3f5", "悬停"),
        ]

        for color, name in colors:
            widget = QWidget()
            widget.setFixedSize(60, 60)
            widget.setStyleSheet(f"""
                QWidget {{
                    background: {color};
                    border-radius: 8px;
                }}
            """)
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; color: #1d2129;")

            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(4)
            wrapper_layout.addWidget(widget)
            wrapper_layout.addWidget(label)

            layout.addWidget(wrapper)

        layout.addStretch()
        group.setLayout(layout)
        return group


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 加载配置
    config = get_config()

    # 设置字体
    font = QFont("PingFang SC, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial", 9)
    app.setFont(font)

    # 应用样式
    app.setStyle("Fusion")
    app.setStyleSheet(config.full_stylesheet)

    print("=" * 60)
    print("🎨 飞书风格配色调试")
    print("=" * 60)
    print(f"✅ 环境: {config.ENV if hasattr(config, 'ENV') else 'test'}")
    print(f"✅ 样式表长度: {len(config.full_stylesheet)} 字符")
    print(f"✅ 应用名称: {config.APP_NAME}")
    print("=" * 60)
    print("💡 检查以下内容是否显示飞书风格配色:")
    print("   - 主色: #3370ff (蓝色)")
    print("   - 圆角: 8-12px")
    print("   - 卡片白色背景, 灰色边框")
    print("   - 侧边栏白色, 选中蓝色背景")
    print("=" * 60)

    window = StyleDebugger()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()