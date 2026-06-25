# ui/components/sidebar.py
"""侧边栏导航组件"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal


class SidebarButton(QPushButton):
    """侧边栏导航按钮"""
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar_btn")
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(f"  {icon}  {text}")
        self.setCheckable(True)
        self.setAutoExclusive(True)


class Sidebar(QWidget):
    """侧边栏"""

    tab_changed = Signal(str)  # 切换标签页信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # Logo
        logo_widget = QWidget()
        logo_widget.setFixedHeight(52)
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel("📊 资产中台")
        logo_label.setObjectName("logo_label")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_widget)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("sidebar_sep")
        layout.addWidget(sep)

        # 导航按钮
        scroll = QScrollArea()
        scroll.setObjectName("sidebar_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 4, 0, 4)
        scroll_layout.setSpacing(2)

        nav_items = [
            ("📊", "仪表盘", "dashboard"),
            ("📁", "资产管理", "assets"),
            ("🧰", "工具箱", "toolbox"),
            ("📈", "报表中心", "reports"),
            ("⚙️", "系统设置", "settings"),
        ]

        self.nav_buttons = {}
        for icon, text, tab_id in nav_items:
            btn = SidebarButton(icon, text)
            btn.clicked.connect(lambda checked, tid=tab_id: self.tab_changed.emit(tid))
            scroll_layout.addWidget(btn)
            self.nav_buttons[tab_id] = btn

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 底部用户信息
        bottom_widget = QWidget()
        bottom_widget.setObjectName("sidebar_bottom")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(2)

        self.user_name_label = QLabel("未登录")
        self.user_name_label.setObjectName("sidebar_user_name")
        self.user_role_label = QLabel("")
        self.user_role_label.setObjectName("sidebar_user_role")

        bottom_layout.addWidget(self.user_name_label)
        bottom_layout.addWidget(self.user_role_label)
        layout.addWidget(bottom_widget)

        # 默认选中仪表盘
        self.set_current_tab("dashboard")

    def set_current_tab(self, tab_id: str):
        """切换选中标签"""
        for tid, btn in self.nav_buttons.items():
            btn.setChecked(tid == tab_id)

    def set_user_info(self, user_info: dict):
        """设置用户信息"""
        if user_info:
            real_name = user_info.get("real_name", "未知用户")
            role = user_info.get("role", 0)
            role_map = {1: "管理员", 2: "运营", 3: "剪辑"}
            role_name = role_map.get(role, f"角色{role}")
            self.user_name_label.setText(f"👤 {real_name}")
            self.user_role_label.setText(role_name)
        else:
            self.user_name_label.setText("未登录")
            self.user_role_label.setText("")