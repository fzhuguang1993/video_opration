# ui/components/collapsible_params_panel.py
"""可折叠参数调节面板"""
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSlider, QCheckBox, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

from widgets.clickable_label import ClickableLabel
from widgets.param_hint_btn import ParamHintButton
from core.config import get_config


class CollapsibleParamsPanel(QWidget):
    """可折叠参数调节面板"""

    params_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.sliders = {}
        self.labels = {}

        # 折叠状态
        self._is_collapsed = True
        self._animation = None

        self._setup_ui()
        self._setup_connections()
        self._set_defaults()

        # 默认折叠
        self.set_collapsed(True)

    def _setup_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== 标题栏（可点击折叠） =====
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QWidget:hover {
                background: rgba(248, 250, 252, 0.95);
                border-color: #cbd5e1;
            }
        """)
        self.header_widget.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(12, 6, 12, 6)
        header_layout.setSpacing(8)

        # 折叠箭头
        self.arrow_label = QLabel("▶")
        self.arrow_label.setStyleSheet("font-size: 12px; color: #6366f1; font-weight: bold;")
        header_layout.addWidget(self.arrow_label)

        # 标题
        title_label = QLabel("⚙️ 参数调节")
        title_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e293b;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 状态标签
        self.status_label = QLabel("点击展开")
        self.status_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        header_layout.addWidget(self.status_label)

        # 提示按钮
        hint_btn = ParamHintButton(
            "参数说明：\n\n"
            "• 右侧边距：水印距离视频右边界的像素\n"
            "• 垂直位置：水印距离视频顶部的像素\n"
            "• 水平速度：碰撞反弹时左右移动的速度\n"
            "• 垂直速度：碰撞反弹时上下移动的速度\n"
            "• 顶部预留：水印不会进入的顶部区域\n"
            "• 底部预留：水印不会进入的底部区域\n\n"
            "💡 双击数值可手动输入"
        )
        header_layout.addWidget(hint_btn)

        main_layout.addWidget(self.header_widget)

        # ===== 内容区域（可折叠） =====
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.9);
                border-left: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
                border-radius: 0 0 8px 8px;
            }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(4)

        # ===== 参数网格 =====
        grid = QGridLayout()
        grid.setVerticalSpacing(self.config.PARAMS_ROW_SPACING)
        grid.setHorizontalSpacing(self.config.PARAMS_COL_SPACING)
        grid.setContentsMargins(4, 4, 4, 4)

        label_style = f"""
            QLabel {{
                font-size: 12px;
                color: #475569;
                min-width: {self.config.PARAMS_LABEL_WIDTH}px;
            }}
        """

        params = [
            ("右侧边距:", "margin", 0, 500, 148, False),
            ("垂直位置:", "y", 1000, 1900, 1602, False),
            ("水平速度:", "speed_x", 1, 100, 5, True),
            ("垂直速度:", "speed_y", 1, 100, 5, True),
            ("顶部预留:", "top_margin", 0, 500, 50, False),
            ("底部预留:", "bottom_margin", 0, 500, 50, False),
        ]

        for row, param in enumerate(params):
            label_text, key, min_val, max_val, default, is_float = param

            label = QLabel(label_text)
            label.setStyleSheet(label_style)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.valueChanged.connect(lambda v, k=key: self._on_slider_changed(k, v))
            grid.addWidget(slider, row, 1)
            self.sliders[key] = slider

            display_value = str(default if not is_float else default / 100)
            label = ClickableLabel(
                display_value,
                min_val,
                max_val,
                is_float=is_float
            )
            label.setFixedWidth(self.config.PARAMS_LABEL_WIDTH + 10)
            label.value_changed.connect(lambda v, k=key: self._on_label_changed(k, v))
            grid.addWidget(label, row, 2)
            self.labels[key] = label

        content_layout.addLayout(grid)

        # ===== 高级选项 =====
        advanced_layout = QHBoxLayout()
        advanced_layout.setContentsMargins(4, 8, 4, 4)
        self.enable_debug = QCheckBox("启用调试模式")
        self.enable_debug.setChecked(False)
        advanced_layout.addWidget(self.enable_debug)
        advanced_layout.addStretch()
        content_layout.addLayout(advanced_layout)

        main_layout.addWidget(self.content_widget)

    def _setup_connections(self):
        """设置信号连接"""
        self.header_widget.mousePressEvent = self._on_header_clicked

    def _on_header_clicked(self, event):
        """点击标题切换折叠状态"""
        self.toggle_collapsed()

    def toggle_collapsed(self):
        """切换折叠状态"""
        self.set_collapsed(not self._is_collapsed)

    def set_collapsed(self, collapsed: bool):
        """设置折叠状态"""
        self._is_collapsed = collapsed

        if collapsed:
            self.content_widget.setVisible(False)
            self.arrow_label.setText("▶")
            self.status_label.setText("点击展开")
            self.header_widget.setStyleSheet("""
                QWidget {
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                }
                QWidget:hover {
                    background: rgba(248, 250, 252, 0.95);
                    border-color: #cbd5e1;
                }
            """)
        else:
            self.content_widget.setVisible(True)
            self.arrow_label.setText("▼")
            self.status_label.setText("点击折叠")
            self.header_widget.setStyleSheet("""
                QWidget {
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid #e2e8f0;
                    border-radius: 8px 8px 0 0;
                }
                QWidget:hover {
                    background: rgba(248, 250, 252, 0.95);
                    border-color: #cbd5e1;
                }
            """)

    def _set_defaults(self):
        """设置默认值"""
        pass

    def _on_slider_changed(self, key: str, value: int):
        """滑块变化"""
        label = self.labels.get(key)
        if label:
            if key in ['speed_x', 'speed_y']:
                label.setText(f"{value / 100:.2f}")
            else:
                label.setText(str(value))
        self._emit_params()

    def _on_label_changed(self, key: str, value: int):
        """标签变化"""
        slider = self.sliders.get(key)
        if slider:
            slider.setValue(value)
        self._emit_params()

    def _emit_params(self):
        """发射参数变化信号"""
        params = self.get_params()
        self.params_changed.emit(params)

    def get_params(self) -> dict:
        """获取当前参数"""
        return {
            'right_margin': self.sliders['margin'].value(),
            'bottom_y': self.sliders['y'].value(),
            'bounce_speed_x': self.sliders['speed_x'].value() / 100,
            'bounce_speed_y': self.sliders['speed_y'].value() / 100,
            'top_margin': self.sliders['top_margin'].value(),
            'bottom_margin': self.sliders['bottom_margin'].value(),
        }

    def set_params(self, params: dict):
        """设置参数"""
        for key, value in params.items():
            if key in self.sliders:
                if key in ['bounce_speed_x', 'bounce_speed_y']:
                    self.sliders[key].setValue(int(value * 100))
                else:
                    self.sliders[key].setValue(value)