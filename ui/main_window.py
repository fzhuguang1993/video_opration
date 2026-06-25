# ui/main_window.py
"""主窗口 - 侧边栏 + 标签页布局"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt, Signal

from core.config import get_config
from core.logger import get_logger
from core.video_service import get_user_video_list

from ui.components.sidebar import Sidebar
from ui.components.top_bar import TopBar
from ui.pages import (
    DashboardPage, AssetsPage, ToolboxPage,
    WatermarkPage, BatchPastePage, ReportsPage, SettingsPage
)


class MainWindow(QMainWindow):
    """主窗口"""

    logout_signal = Signal()

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.logger = get_logger("main_window")

        self.current_user = None
        self._logout_triggered = False

        self.logger.info("初始化主窗口")
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """设置窗口"""
        self.setWindowTitle(self.config.window_title)
        self.setMinimumSize(
            self.config.WINDOW_MIN_WIDTH,
            self.config.WINDOW_MIN_HEIGHT
        )
        self.resize(
            self.config.WINDOW_DEFAULT_WIDTH,
            self.config.WINDOW_DEFAULT_HEIGHT
        )

    def _setup_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ===== 顶部栏 =====
        self.top_bar = TopBar(self.config)
        self.top_bar.logout_clicked.connect(self._on_logout)
        main_layout.addWidget(self.top_bar)

        # ===== 主体区域（侧边栏 + 内容） =====
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)

        # 侧边栏
        self.sidebar = Sidebar()
        self.sidebar.tab_changed.connect(self._switch_tab)
        body_layout.addWidget(self.sidebar)

        # 内容区域
        content_widget = QWidget()
        content_widget.setObjectName("content_area")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # StackedWidget 管理所有页面
        self.stack = QStackedWidget()

        # 创建页面
        self.pages = {
            "dashboard": DashboardPage(),
            "assets": AssetsPage(),
            "toolbox": ToolboxPage(),
            "watermark": WatermarkPage(),
            "batch_paste": BatchPastePage(),
            "reports": ReportsPage(),
            "settings": SettingsPage(),
        }

        # 添加到Stack
        for page in self.pages.values():
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        body_layout.addWidget(content_widget, 1)

        main_layout.addWidget(body)

        # 默认显示仪表盘
        self._switch_tab("dashboard")

        self.statusBar().showMessage("就绪")

    # ui/main_window.py - 在 set_current_user 方法中添加

    def set_current_user(self, user_info: dict):
        """设置当前用户"""
        self.current_user = user_info
        self.logger.info(f"设置当前用户: {user_info.get('real_name')}")

        # 更新顶部栏
        self.top_bar.set_user_info(user_info)

        # 更新侧边栏
        self.sidebar.set_user_info(user_info)

        # ✅ 传递用户信息到各个页面
        for page in self.pages.values():
            if hasattr(page, 'set_current_user'):
                page.set_current_user(user_info)

        # 更新窗口标题
        real_name = user_info.get("real_name", "未知")
        role = user_info.get("role", 0)
        role_map = {1: "管理员", 2: "运营", 3: "剪辑"}
        role_name = role_map.get(role, f"角色{role}")
        self.setWindowTitle(
            f"{self.config.APP_ICON} {self.config.APP_NAME} v{self.config.APP_VERSION}  姓名:{real_name}  岗位:{role_name}"
        )

    def _switch_tab(self, tab_id: str):
        """切换标签页"""
        self.logger.info(f"切换到: {tab_id}")

        # 如果是工具箱，特殊处理
        if tab_id == "toolbox":
            # 显示工具箱页面，连接工具选择信号
            toolbox_page = self.pages["toolbox"]
            toolbox_page.tool_selected.connect(self._on_tool_selected)
            self.stack.setCurrentWidget(toolbox_page)
        else:
            # 直接切换页面
            if tab_id in self.pages:
                self.stack.setCurrentWidget(self.pages[tab_id])

    def _on_tool_selected(self, tool_id: str):
        """工具被选中"""
        self.logger.info(f"选择工具: {tool_id}")
        if tool_id == "watermark":
            self.sidebar.set_current_tab("toolbox")
            self.stack.setCurrentWidget(self.pages["watermark"])
        elif tool_id == "batch_paste":
            self.sidebar.set_current_tab("toolbox")
            self.stack.setCurrentWidget(self.pages["batch_paste"])

    def _on_logout(self):
        """登出"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认登出",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.logger.info(f"用户登出")
            self._logout_triggered = True
            self.logout_signal.emit()
            self.close()

    def closeEvent(self, event):
        """关闭事件"""
        self.config.save()
        self.logger.info("主窗口关闭")
        event.accept()