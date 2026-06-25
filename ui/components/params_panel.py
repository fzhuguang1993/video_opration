# ui/components/params_panel.py
"""参数调节面板 - 独立组件"""
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from widgets.clickable_label import ClickableLabel
from widgets.param_hint_btn import ParamHintButton
from core.config import get_config


class ParamsPanel(QGroupBox):
    """参数调节面板"""

    # 参数变化信号
    params_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__("⚙️ 参数调节", parent)
        self.config = get_config()
        self.sliders = {}
        self.labels = {}
        self._setup_ui()
        self._set_defaults()

    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # 设置最小/最大高度 - 使用配置
        self.setMinimumHeight(self.config.PARAMS_PANEL_MIN_HEIGHT)
        self.setMaximumHeight(self.config.PARAMS_PANEL_MAX_HEIGHT)

        # ===== 参数标题栏 =====
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)

        # 标题 - 使用配置的文字
        title_label = QLabel(self.config.PARAMS_TITLE_TEXT)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: {self.config.PARAMS_TITLE_FONT_WEIGHT};
                font-size: {self.config.PARAMS_TITLE_FONT_SIZE}px;
                color: #1e293b;
            }}
        """)
        header.addWidget(title_label)
        header.addStretch()

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
        header.addWidget(hint_btn)
        layout.addLayout(header)

        # ===== 参数网格 =====
        grid = QGridLayout()
        # ✅ 使用配置中的间距值
        grid.setVerticalSpacing(self.config.PARAMS_ROW_SPACING)
        grid.setHorizontalSpacing(self.config.PARAMS_COL_SPACING)
        grid.setContentsMargins(4, 4, 4, 4)

        # 标签样式 - 使用配置的宽度
        label_style = f"""
            QLabel {{
                font-size: 12px;
                color: #475569;
                min-width: {self.config.PARAMS_LABEL_WIDTH}px;
            }}
        """

        # (标签, key, 最小值, 最大值, 默认值, 是否为浮点数)
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

            # 标签 - 应用样式
            label = QLabel(label_text)
            label.setStyleSheet(label_style)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)

            # 滑块
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.valueChanged.connect(lambda v, k=key: self._on_slider_changed(k, v))
            grid.addWidget(slider, row, 1)
            self.sliders[key] = slider

            # 数值标签（可点击编辑）
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

        layout.addLayout(grid)

        # 高级选项
        advanced_layout = QHBoxLayout()
        advanced_layout.setContentsMargins(4, 8, 4, 4)
        self.enable_debug = QCheckBox("启用调试模式")
        self.enable_debug.setChecked(False)
        advanced_layout.addWidget(self.enable_debug)
        advanced_layout.addStretch()
        layout.addLayout(advanced_layout)

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