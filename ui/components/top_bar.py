# ui/components/top_bar.py
"""顶部栏组件"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Signal


class TopBar(QWidget):
    """顶部栏"""

    logout_clicked = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("top_bar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # 标题
        title = QLabel(f"{self.config.APP_ICON} {self.config.APP_NAME}")
        title.setObjectName("top_bar_title")
        layout.addWidget(title)

        layout.addStretch()

        # 用户信息
        self.user_label = QLabel("未登录")
        self.user_label.setObjectName("top_bar_user")
        layout.addWidget(self.user_label)

        # 登出按钮
        self.logout_btn = QPushButton("登出")
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.clicked.connect(self.logout_clicked)
        self.logout_btn.setVisible(False)
        layout.addWidget(self.logout_btn)

    def set_user_info(self, user_info: dict):
        """设置用户信息"""
        if user_info:
            real_name = user_info.get("real_name", "未知用户")
            role = user_info.get("role", 0)
            role_map = {1: "管理员", 2: "运营", 3: "剪辑"}
            role_name = role_map.get(role, f"角色{role}")
            self.user_label.setText(f"👤 {real_name}  |  {role_name}")
            self.logout_btn.setVisible(True)
        else:
            self.user_label.setText("未登录")
            self.logout_btn.setVisible(False)