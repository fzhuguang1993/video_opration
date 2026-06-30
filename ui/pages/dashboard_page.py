# ui/pages/dashboard_page.py
"""仪表盘页面"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

from config import DB_CFG
from core.logger import get_logger
import pymysql
from core.database import get_connection


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.logger = get_logger("dashboard_page")
        self._setup_ui()

    def set_current_user(self, user_info: dict):
        self.current_user = user_info
        self._refresh_stats()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("📊 仪表盘")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("溯源视频数据概览")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # 统计卡片
        self.card_layout = QHBoxLayout()
        self.card_layout.setSpacing(12)
        layout.addLayout(self.card_layout)

        # 初始化卡片
        self._init_cards()

        # 额外信息
        info_label = QLabel("💡 数据说明：溯源码池 = 可用溯源码数量 | 已绑定 = 溯源码绑定关系数量")
        info_label.setStyleSheet("color: #868e96; font-size: 12px; padding-top: 8px;")
        layout.addWidget(info_label)

        layout.addStretch()

    def _init_cards(self):
        # 清空旧卡片
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 从数据库获取实际数据
        stats = self._fetch_stats()

        cards = [
            ("📹", "溯源视频总数", str(stats.get("video_trace", 0)), "#5e6ad2"),
            ("📦", "溯源码池剩余", str(stats.get("code_pool_available", 0)), "#10b981"),
            ("🔗", "已绑定关系", str(stats.get("video_bind", 0)), "#f59e0b"),
            ("👤", "剪辑人员", str(stats.get("editor_count", 0)), "#ec4899"),
            ("🏷️", "已用溯源码", str(stats.get("code_pool_used", 0)), "#8b5cf6"),
        ]

        for icon, label, value, color in cards:
            card = self._create_stat_card(icon, label, value, color)
            self.card_layout.addWidget(card)

    def _fetch_stats(self) -> dict:
        """从数据库获取统计数据"""
        stats = {
            "video_trace": 0,
            "code_pool_available": 0,
            "code_pool_used": 0,
            "video_bind": 0,
            "editor_count": 0,
        }

        conn = None
        cur = None
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            # 溯源视频总数
            cur.execute("SELECT COUNT(*) FROM video_trace")
            stats["video_trace"] = cur.fetchone()[0] or 0

            # 溯源码池可用
            cur.execute("SELECT COUNT(*) FROM trace_code_pool WHERE is_used = 0")
            stats["code_pool_available"] = cur.fetchone()[0] or 0

            # 溯源码池已用
            cur.execute("SELECT COUNT(*) FROM trace_code_pool WHERE is_used = 1")
            stats["code_pool_used"] = cur.fetchone()[0] or 0

            # 绑定关系
            cur.execute("SELECT COUNT(*) FROM video_bind")
            stats["video_bind"] = cur.fetchone()[0] or 0

            # 剪辑人员（role=3）
            cur.execute("SELECT COUNT(*) FROM sys_user WHERE role = 3")
            stats["editor_count"] = cur.fetchone()[0] or 0

        except Exception as e:
            self.logger.error(f"获取统计数据失败: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        return stats

    def _refresh_stats(self):
        """刷新统计数据"""
        self._init_cards()

    def _create_stat_card(self, icon: str, label: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat_card")
        card.setStyleSheet(f"""
            QFrame#stat_card {{
                background: white;
                border-radius: 8px;
                padding: 16px;
                min-height: 80px;
                border-left: 4px solid {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        label_widget = QLabel(f"{icon}  {label}")
        label_widget.setObjectName("stat_label")
        value_widget = QLabel(value)
        value_widget.setObjectName("stat_value")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return card