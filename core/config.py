# core/config.py
"""应用配置管理 - Linear 风格"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import os

# ================================================================
# 🌍 环境配置
# ================================================================
ENV = "test"  # "test" 或 "production"
ENABLE_CONFIG_CACHE = ENV == "production"


@dataclass
class AppConfig:
    """应用配置"""
    # 应用信息
    APP_NAME: str = "运营部数据资产中台"
    APP_VERSION: str = "2.0.0"
    APP_ICON: str = "📊"

    # 窗口大小
    WINDOW_MIN_WIDTH: int = 1200
    WINDOW_MIN_HEIGHT: int = 750
    WINDOW_DEFAULT_WIDTH: int = 1350
    WINDOW_DEFAULT_HEIGHT: int = 880

    # 侧边栏宽度
    SIDEBAR_WIDTH: int = 200

    # 参数面板大小
    PARAMS_PANEL_MIN_HEIGHT: int = 280
    PARAMS_PANEL_MAX_HEIGHT: int = 400

    # 视频列表高度
    VIDEO_TABLE_MIN_HEIGHT: int = 400

    # 日志面板高度
    LOG_PANEL_MAX_HEIGHT: int = 120
    LOG_PANEL_MIN_HEIGHT: int = 80

    # 默认路径
    DEFAULT_FOLDER: str = "/Users/leiliang/Desktop/movie_space"
    DEFAULT_WATERMARK: str = "/Users/leiliang/Desktop/movie_space/水印/shuiyin.png"

    # 分页
    PAGE_SIZE: int = 20

    # 参数面板配置
    PARAMS_ROW_SPACING: int = 10
    PARAMS_COL_SPACING: int = 8
    PARAMS_LABEL_WIDTH: int = 60
    PARAMS_TITLE_TEXT: str = "参数调节"
    PARAMS_TITLE_FONT_SIZE: int = 13
    PARAMS_TITLE_FONT_WEIGHT: str = "600"

    # 工具面板配置
    TOOL_PANEL_MIN_HEIGHT: int = 150
    TOOL_PANEL_MAX_HEIGHT: int = 250
    TOOL_GRID_SPACING: int = 6
    TOOL_GRID_COLS: int = 4
    TOOL_MAX_BUTTONS: int = 7
    TOOL_BUTTON_MIN_HEIGHT: int = 32

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        """从文件加载配置 - 测试环境直接返回默认值"""
        if ENV == "test":
            print("🔧 测试环境：使用默认配置（忽略缓存）")
            return cls()

        if config_path is None:
            config_path = Path.home() / ".movie_config.json"

        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    return cls(**data)
            except:
                pass
        return cls()

    def save(self, config_path: Optional[Path] = None):
        """保存配置 - 测试环境不保存"""
        if ENV == "test":
            print("🔧 测试环境：配置不保存（缓存已禁用）")
            return

        if config_path is None:
            config_path = Path.home() / ".movie_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    @property
    def window_title(self) -> str:
        return f"{self.APP_ICON} {self.APP_NAME} v{self.APP_VERSION}"

    # ================================================================
    # 🎨 Linear 风格样式表
    # ================================================================

    # ... existing code ...
    @property
    def full_stylesheet(self) -> str:
        """完整的样式表 - Linear 风格"""
        return "\n".join([
            self.style_global,
            self.style_sidebar,
            self.style_topbar,
            self.style_pages,
            self.style_cards,
            self.style_groupbox,
            self.style_buttons,
            self.style_inputs,
            self.style_combobox,
            self.style_slider_progress,
            self.style_table,
            self.style_table_rows,
            self.style_assets_table,
            self.style_assets_tab,
            self.style_trace_tab,
            self.style_checkbox,
            self.style_menu,
            self.style_scrollbar,
            self.style_labels,
            self.style_toolbutton,
            self.style_statusbar,
            self.style_log_text,
            self.style_login_dialog,
        ])
    # ... existing code ...


    # 表格样式

    # ===== 全局 =====
    @property
    def style_global(self) -> str:
        return """
            QMainWindow {
                background: #f5f6f8;
            }
            QWidget {
                background: transparent;
                color: #1a1a2e;
                font-size: 12px;
                font-family: "Inter", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
            }
            QDialog {
                background: #f5f6f8;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """

    # ===== 侧边栏 =====
    @property
    def style_sidebar(self) -> str:
        return """
            QWidget#sidebar {
                background: #ffffff;
                border-right: 1px solid #e6e7ea;
            }
            QLabel#logo_label {
                color: #1a1a2e;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }
            QFrame#sidebar_sep {
                background: #e6e7ea;
                max-height: 1px;
                margin: 4px 12px;
            }
            QPushButton#sidebar_btn {
                background: transparent;
                color: #4a4a5a;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                min-height: 38px;
                margin: 1px 6px;
            }
            QPushButton#sidebar_btn:hover {
                background: #f1f2f4;
                color: #1a1a2e;
            }
            QPushButton#sidebar_btn:checked {
                background: #ebecef;
                color: #5e6ad2;
                font-weight: 600;
            }
            QWidget#sidebar_bottom {
                background: #f5f6f8;
                border-radius: 6px;
                margin: 8px 6px;
                padding: 10px;
            }
            QLabel#sidebar_user_name {
                color: #1a1a2e;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#sidebar_user_role {
                color: #8a8a9a;
                font-size: 11px;
            }
        """

    # ===== 顶部栏 =====
    @property
    def style_topbar(self) -> str:
        return """
            QWidget#top_bar {
                background: #ffffff;
                border-bottom: 1px solid #e6e7ea;
                min-height: 50px;
                padding: 0 20px;
            }
            QLabel#top_bar_title {
                color: #1a1a2e;
                font-size: 17px;
                font-weight: 700;
            }
            QLabel#top_bar_user {
                color: #4a4a5a;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#logout_btn {
                background: #f5f6f8;
                color: #4a4a5a;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 5px 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#logout_btn:hover {
                background: #fef2f2;
                color: #eb5757;
                border-color: #fccccc;
            }
        """

    # ===== 页面 =====
    @property
    def style_pages(self) -> str:
        return """
            QLabel#page_title {
                font-size: 22px;
                font-weight: 700;
                color: #1a1a2e;
                padding-bottom: 10px;
                letter-spacing: -0.2px;
            }
            QLabel#page_subtitle {
                font-size: 13px;
                color: #8a8a9a;
                padding-bottom: 16px;
            }
        """

    # ===== 卡片 =====
    @property
    def style_cards(self) -> str:
        return """
            QFrame#tool_card {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                padding: 20px;
                min-height: 100px;
            }
            QFrame#tool_card:hover {
                border-color: #5e6ad2;
            }
            QLabel#tool_card_icon {
                font-size: 26px;
            }
            QLabel#tool_card_title {
                font-size: 14px;
                font-weight: 600;
                color: #1a1a2e;
            }
            QLabel#tool_card_desc {
                font-size: 12px;
                color: #8a8a9a;
            }
            QFrame#stat_card {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                padding: 18px;
                min-height: 80px;
            }
            QLabel#stat_label {
                font-size: 13px;
                color: #8a8a9a;
            }
            QLabel#stat_value {
                font-size: 26px;
                font-weight: 700;
                color: #1a1a2e;
            }
        """

    # ===== 分组框 =====
    @property
    def style_groupbox(self) -> str:
        return """
            QGroupBox {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                padding-bottom: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px;
                color: #1a1a2e;
                font-weight: 600;
                font-size: 12px;
            }
        """

    # ===== 按钮 =====
    @property
    def style_buttons(self) -> str:
        return """
            QPushButton {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 7px 18px;
                color: #4a4a5a;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f5f6f8;
                border-color: #d5d6db;
            }
            QPushButton:pressed {
                background: #e6e7ea;
            }
            QPushButton:disabled {
                background: #f5f6f8;
                color: #b0b0bc;
            }

            QPushButton#primary_btn {
                background: #5e6ad2;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                padding: 8px 22px;
            }
            QPushButton#primary_btn:hover {
                background: #4f5bc9;
            }
            QPushButton#primary_btn:pressed {
                background: #424ebd;
            }
            QPushButton#primary_btn:disabled {
                background: #b8bff0;
                color: #edeefb;
            }

            QPushButton#success_btn {
                background: #0f766e;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                padding: 7px 18px;
            }
            QPushButton#success_btn:hover {
                background: #118278;
            }

            QPushButton#danger_btn {
                background: #eb5757;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                padding: 7px 18px;
            }
            QPushButton#danger_btn:hover {
                background: #ee6a6a;
            }

            QPushButton#ghost_btn {
                background: transparent;
                border: 1px solid #e6e7ea;
                padding: 4px 12px;
                color: #4a4a5a;
            }
            QPushButton#ghost_btn:hover {
                background: #f5f6f8;
                padding: 4px 12px;
                border-color: #d5d6db;
            }

            QPushButton#start_btn {
                background: #5e6ad2;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 12px 28px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton#start_btn:hover {
                background: #4f5bc9;
            }
            QPushButton#start_btn:disabled {
                background: #b8bff0;
                color: #edeefb;
            }
        """

    # ===== 输入框 =====
    @property
    def style_inputs(self) -> str:
        return """
            QLineEdit, QTextEdit, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 7px 14px;
                color: #1a1a2e;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5e6ad2;
                outline: none;
            }
            QLineEdit:disabled, QTextEdit:disabled {
                background: #f5f6f8;
                color: #b0b0bc;
            }
            QLineEdit::placeholder {
                color: #b0b0bc;
            }
            QLineEdit#search_input {
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                background: #f5f6f8;
            }
            QLineEdit#search_input:focus {
                border-color: #5e6ad2;
                background: #ffffff;
            }
        """

    # ===== 下拉框 =====
    @property
    def style_combobox(self) -> str:
        return """
            QComboBox {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 6px 14px;
                color: #1a1a2e;
                min-height: 28px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #d5d6db;
            }
            QComboBox:on {
                border-color: #5e6ad2;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 6px;
                selection-background-color: #ebecef;
                selection-color: #5e6ad2;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #f5f6f8;
            }
            QComboBox:disabled {
                background: #f5f6f8;
                color: #b0b0bc;
            }
        """

    # ===== 滑块和进度条 =====
    @property
    def style_slider_progress(self) -> str:
        return """
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #e6e7ea;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #5e6ad2;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #4f5bc9;
                width: 18px;
                height: 18px;
                margin: -7px 0;
            }
            QSlider::sub-page:horizontal {
                background: #5e6ad2;
                border-radius: 2px;
            }

            QProgressBar {
                background: #e6e7ea;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: #1a1a2e;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: #5e6ad2;
                border-radius: 4px;
            }
        """

    # ===== 表格 =====
    @property
    def style_table(self) -> str:
        return """
            QTableWidget {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                gridline-color: #f1f2f4;
                alternate-background-color: #fafafb;
                outline: none;
            }
            QTableWidget:focus {
                border-color: #5e6ad2;
            }
            QHeaderView::section {
                background: #f5f6f8;
                padding: 10px 14px;
                border: none;
                border-bottom: 2px solid #e6e7ea;
                font-weight: 600;
                color: #4a4a5a;
                font-size: 11px;
            }
            QHeaderView::section:hover {
                background: #e6e7ea;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
                color: #1a1a2e;
                font-size: 12px;
            }
            QTableWidget::item:alternate {
                background: #fafafb;
            }
            QTableWidget::item:hover {
                background: #f1f2f4;
            }
            QTableWidget::item:selected {
                background: #ebecef;
                color: #1a1a2e;
            }
            QTableWidget::item:disabled {
                color: #b0b0bc;
            }
        """

    # ===== 资产管理表格 =====
    @property
    def style_assets_table(self) -> str:
        return """
            QTableWidget#assets_table {
                border: none;
                gridline-color: #f1f2f4;
                alternate-background-color: #fafafb;
                background-color: #ffffff;
            }
            QTableWidget#assets_table::item {
                padding: 4px 8px;
                font-size: 12px;
            }
            QTableWidget#assets_table::item:selected {
                background-color: #ebecef;
            }
            /* ✅ 修复编辑框高度 */
            QTableWidget#assets_table QLineEdit {
                min-height: 28px;
                max-height: 28px;
                padding: 2px 6px;
                font-size: 12px;
                border: 1px solid #5e6ad2;
                border-radius: 4px;
                background: white;
            }
            
            /* ✅ 修复编辑框在 Mac 上的高度问题 */
            QTableWidget#assets_table QWidget {
                min-height: 28px;
            }
            QTableWidget#assets_table QHeaderView::section {
                background: #f5f6f8;
                padding: 6px 10px;
                border: none;
                border-bottom: 2px solid #e6e7ea;
                font-weight: 600;
                color: #4a4a5a;
                font-size: 11px;
            }
        """

    # ===== Tab 样式 =====
    # ... existing code ...
    # ===== Tab 样式 =====
    @property
    def style_assets_tab(self) -> str:
        return """
            QTabWidget#assets_tab_widget::pane {
                background: white;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                padding: 8px;
            }
            QTabWidget#assets_tab_widget QTabBar::tab {
                background: #f8f9fa;
                color: #495057;
                border: 1px solid #e6e7ea;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 500;
                margin-right: 2px;
                min-width: 60px;
            }
            QTabWidget#assets_tab_widget QTabBar::tab:selected {
                background: #ebecef;
                color: #5e6ad2;
                font-weight: 600;
            }
            QTabWidget#assets_tab_widget QTabBar::tab:hover {
                background: #f1f2f4;
            }
        """

    @property
    def style_trace_tab(self) -> str:
        return """
               QTabWidget#trace_tab_widget::pane {
                   background: white;
                   border: 1px solid #e6e7ea;
                   border-radius: 8px;
                   padding: 8px;
               }
               QTabWidget#trace_tab_widget QTabBar::tab {
                   background: #f8f9fa;
                   color: #495057;
                   border: 1px solid #e6e7ea;
                   border-bottom: none;
                   border-radius: 6px 6px 0 0;
                   padding: 8px 18px;
                   font-size: 12px;
                   font-weight: 500;
                   margin-right: 2px;
                   min-width: 60px;
               }
               QTabWidget#trace_tab_widget QTabBar::tab:selected {
                   background: #ebecef;
                   color: #5e6ad2;
                   font-weight: 600;
               }
               QTabWidget#trace_tab_widget QTabBar::tab:hover {
                   background: #f1f2f4;
               }
           """

    # ===== 表格行 =====
    @property
    def style_table_rows(self) -> str:
        return """
            QTableWidget::item[data_role="bind"] {
                background: #edeefb;
            }
            QTableWidget::item[data_role="bind"]:hover {
                background: #dddff7;
            }
            QTableWidget::item[data_role="bind"]:selected {
                background: #c6caf0;
            }
            QTableWidget::item[data_role="host"] {
                background: #fef2f2;
            }
            QTableWidget::item[data_role="host"]:hover {
                background: #fee2e2;
            }
            QTableWidget::item[data_role="host"]:selected {
                background: #fecaca;
            }
            QTableWidget::item[data_role="warning"] {
                background: #fff7e6;
            }
            QTableWidget::item[data_role="warning"]:hover {
                background: #ffedcc;
            }
            QTableWidget::item[data_role="warning"]:selected {
                background: #ffd899;
            }
            QTableWidget::item[data_role="success"] {
                background: #e6f7f2;
            }
            QTableWidget::item[data_role="success"]:hover {
                background: #d1f0e8;
            }
            QTableWidget::item[data_role="success"]:selected {
                background: #ade9d8;
            }
            QTableWidget::item[data_role="error"] {
                background: #fef2f2;
            }
            QTableWidget::item[data_role="error"]:hover {
                background: #fee2e2;
            }
            QTableWidget::item[data_role="error"]:selected {
                background: #fecaca;
            }
        """

    # ===== 复选框 =====
    @property
    def style_checkbox(self) -> str:
        return """
            QCheckBox {
                spacing: 8px;
                color: #1a1a2e;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid #b0b0bc;
                background: #ffffff;
            }
            QCheckBox::indicator:checked {
                background: #5e6ad2;
                border-color: #5e6ad2;
            }
            QCheckBox::indicator:hover {
                border-color: #5e6ad2;
            }
            QCheckBox::indicator:disabled {
                background: #f5f6f8;
                border-color: #e6e7ea;
            }
        """

    # ===== 菜单 =====
    @property
    def style_menu(self) -> str:
        return """
            QMenu {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 6px 0px;
            }
            QMenu::item {
                padding: 8px 26px;
                background: transparent;
                color: #1a1a2e;
                font-size: 12px;
            }
            QMenu::item:selected {
                background: #ebecef;
                color: #5e6ad2;
            }
            QMenu::separator {
                height: 1px;
                background: #e6e7ea;
                margin: 4px 12px;
            }
        """

    # ===== 滚动条 =====
    @property
    def style_scrollbar(self) -> str:
        return """
            QScrollBar:vertical {
                background: #f5f6f8;
                width: 6px;
                border-radius: 3px;
                margin: 3px;
            }
            QScrollBar::handle:vertical {
                background: #b0b0bc;
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8a8a9a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #f5f6f8;
                height: 6px;
                border-radius: 3px;
                margin: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #b0b0bc;
                border-radius: 3px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #8a8a9a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """

    # ===== 标签 =====
    @property
    def style_labels(self) -> str:
        return """
            QLabel {
                color: #1a1a2e;
            }
            QLabel#stats_label {
                color: #8a8a9a;
                font-size: 12px;
            }
            QLabel#page_label {
                color: #4a4a5a;
                font-size: 12px;
                font-weight: 500;
            }
            QLabel#info_label {
                color: #8a8a9a;
                font-size: 12px;
            }
            QLabel#search_label {
                color: #8a8a9a;
                font-size: 13px;
            }
            QLabel#login_title {
                font-size: 30px;
                font-weight: 700;
                color: #1a1a2e;
                letter-spacing: -0.3px;
            }
            QLabel#login_subtitle {
                font-size: 14px;
                color: #8a8a9a;
            }
            QLabel#login_error {
                color: #eb5757;
                font-size: 12px;
                padding: 6px 10px;
                background: #fef2f2;
                border-radius: 6px;
            }
        """

    # ===== 工具按钮 =====
    @property
    def style_toolbutton(self) -> str:
        return """
            QToolButton {
                background: transparent;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 5px 12px;
                color: #4a4a5a;
            }
            QToolButton:hover {
                background: #f5f6f8;
                border-color: #d5d6db;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """

    # ===== 状态栏 =====
    @property
    def style_statusbar(self) -> str:
        return """
            QStatusBar {
                background: transparent;
                color: #8a8a9a;
                font-size: 11px;
                padding: 6px 14px;
            }
        """

    # ===== 日志 =====
    @property
    def style_log_text(self) -> str:
        return """
            QTextEdit#log_text {
                background-color: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                font-family: "Menlo", "Consolas", monospace;
                font-size: 11px;
                padding: 10px;
            }
        """

    # ===== 登录对话框 =====
    @property
    def style_login_dialog(self) -> str:
        return """
            QDialog#login_dialog {
                background: #ffffff;
            }
            QFrame#login_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5e6ad2, stop:1 #7c6fd2);
            }
            QLabel#login_title {
                font-size: 24px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: -0.3px;
            }
            QLabel#login_subtitle {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.75);
            }
            QFrame#login_body {
                background: #ffffff;
            }
            QLabel#login_field_label {
                font-size: 13px;
                font-weight: 600;
                color: #1a1a2e;
                padding-bottom: 2px;
            }
            QLineEdit#login_input {
                background: #f5f6f8;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                padding: 0 16px;
                color: #1a1a2e;
                font-size: 14px;
            }
            QLineEdit#login_input:focus {
                border-color: #5e6ad2;
                background: #ffffff;
            }
            QLineEdit#login_input::placeholder {
                color: #b0b0bc;
            }
            QLabel#login_error {
                color: #eb5757;
                font-size: 12px;
                padding: 8px 12px;
                background: #fef2f2;
                border-radius: 6px;
                border: 1px solid #fccccc;
            }
            QPushButton#login_btn {
                background: #5e6ad2;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 2px;
            }
            QPushButton#login_btn:hover {
                background: #4f5bc9;
            }
            QPushButton#login_btn:pressed {
                background: #424ebd;
            }
            QPushButton#login_link_btn {
                background: transparent;
                color: #8a8a9a;
                border: none;
                font-size: 13px;
                padding: 4px 8px;
            }
            QPushButton#login_link_btn:hover {
                color: #5e6ad2;
            }

            QDialog#change_pwd_dialog {
                background: #ffffff;
            }
            QFrame#change_pwd_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5e6ad2, stop:1 #7c6fd2);
            }
            QLabel#change_pwd_title {
                font-size: 20px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#change_pwd_subtitle {
                font-size: 12px;
                color: rgba(255, 255, 255, 0.7);
            }
            QFrame#change_pwd_body {
                background: #ffffff;
            }
            QLabel#field_label {
                font-size: 13px;
                font-weight: 600;
                color: #1a1a2e;
                padding-bottom: 2px;
            }
            QLineEdit#field_input {
                background: #f5f6f8;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                padding: 0 14px;
                color: #1a1a2e;
                font-size: 14px;
            }
            QLineEdit#field_input:focus {
                border-color: #5e6ad2;
                background: #ffffff;
            }
            QPushButton#change_pwd_ok_btn {
                background: #5e6ad2;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#change_pwd_ok_btn:hover {
                background: #4f5bc9;
            }
            QPushButton#change_pwd_cancel_btn {
                background: #f5f6f8;
                color: #4a4a5a;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#change_pwd_cancel_btn:hover {
                background: #ebecef;
            }
        """

    # ... existing code ...



# 单例配置
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config