# ui/pages/assets_page.py
"""资产管理页面 - 按剪辑人员分 Tab"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

from core.logger import get_logger
from config import DB_CFG
import pymysql
from datetime import datetime


class AssetsPage(QWidget):
    """资产管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("assets_page")
        self.current_user = None
        self.editors = []
        self.all_data = []
        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user_info: dict):
        self.current_user = user_info
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("📁 资产管理")
        title.setObjectName("page_title")
        layout.addWidget(title)

        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("assets_tab_widget")
        self.tab_widget.addTab(self._create_empty_tab(), "加载中...")
        layout.addWidget(self.tab_widget)

    def _create_empty_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("加载数据中...")
        label.setObjectName("page_subtitle")
        layout.addWidget(label)
        return widget

    def _create_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        toolbar.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("搜索文件名/运营...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        import_btn = QPushButton("📥 导入")
        import_btn.setObjectName("primary_btn")
        import_btn.clicked.connect(self._on_import)
        toolbar.addWidget(import_btn)

        export_btn = QPushButton("📤 导出")
        export_btn.setObjectName("ghost_btn")
        export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(export_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setObjectName("ghost_btn")
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        return toolbar

    def _create_pagination_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.setObjectName("ghost_btn")
        self.prev_btn.setFixedWidth(80)
        self.prev_btn.clicked.connect(self._prev_page)

        self.page_label = QLabel("第 1/1 页")
        self.page_label.setObjectName("stats_label")
        self.page_label.setFixedWidth(80)
        self.page_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.setObjectName("ghost_btn")
        self.next_btn.setFixedWidth(80)
        self.next_btn.clicked.connect(self._next_page)

        layout.addStretch()
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_btn)
        layout.addStretch()

        return widget

    # ui/pages/assets_page.py - _load_data 方法

    def _load_data(self):
        try:
            self.logger.info("加载资产管理数据...")
            self.current_page = 1

            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            cur.execute("""
                SELECT id, real_name 
                FROM sys_user 
                WHERE role = 3 
                ORDER BY real_name
            """)
            self.editors = cur.fetchall()

            # ✅ 关联 video_stat 表获取统计数据
            cur.execute("""
                SELECT 
                    vt.id,
                    vt.trace_code,
                    vt.video_path,
                    vt.record_date,
                    editor.real_name AS editor_name,
                    operator.real_name AS operator_name,
                    vs.total_cost,
                    vs.daily_cost,
                    vs.week_cost,
                    vs.impression_count,
                    vs.click_count,
                    vs.click_rate,
                    vs.conversion_count,
                    vs.conversion_rate,
                    vs.cpm_data,
                    vs.three_sec_rate,
                    vs.five_sec_rate,
                    vs.video_rating
                FROM video_trace vt
                LEFT JOIN sys_user editor ON vt.user_id = editor.id
                LEFT JOIN sys_user operator ON vt.operator_id = operator.id
                LEFT JOIN video_stat vs ON vt.trace_code COLLATE utf8mb4_unicode_ci = vs.trace_code COLLATE utf8mb4_unicode_ci
                ORDER BY vt.record_date DESC
            """)
            self.all_data = cur.fetchall()

            cur.close()
            conn.close()

            self.total_pages = max(1, (len(self.all_data) + self.page_size - 1) // self.page_size)
            self._rebuild_tabs()
            self.logger.info(f"加载完成: {len(self.all_data)} 条视频, {len(self.editors)} 个剪辑")

        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")

    def _get_page_data(self, data: list) -> list:
        start = (self.current_page - 1) * self.page_size
        end = min(start + self.page_size, len(data))
        return data[start:end]

    def _rebuild_tabs(self):
        self.tab_widget.clear()

        overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(overview_tab, "总览")

        for editor_id, editor_name in self.editors:
            count = sum(1 for row in self.all_data if row[4] == editor_name)
            tab_title = f"{editor_name} ({count})" if count > 0 else editor_name
            tab = self._create_editor_tab(editor_id, editor_name)
            self.tab_widget.addTab(tab, tab_title)

        self._update_page_label()

    def _create_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        total = len(self.all_data)
        editor_count = len(self.editors)

        card_layout = QHBoxLayout()
        card_layout.setSpacing(12)

        cards = [
            ("📹", "视频总数", str(total), "#5e6ad2"),
            ("✂️", "剪辑人员", str(editor_count), "#10b981"),
            ("📅", "今日新增", self._get_today_count(), "#f59e0b"),
        ]

        for icon, label, value, color in cards:
            card = self._create_stat_card(icon, label, value, color)
            card_layout.addWidget(card)

        card_layout.addStretch()
        layout.addLayout(card_layout)

        label = QLabel("📋 最近视频")
        label.setObjectName("stats_label")
        label.setStyleSheet("font-weight: 600; font-size: 13px;")  # 只有这一个保留，因为 config 里没有这个样式
        layout.addWidget(label)

        table = self._create_data_table()
        page_data = self._get_page_data(self.all_data)
        self._fill_table(table, page_data)
        layout.addWidget(table)

        pagination = self._create_pagination_widget()
        layout.addWidget(pagination)

        return widget

    def _create_editor_tab(self, editor_id: int, editor_name: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        editor_data = [row for row in self.all_data if row[4] == editor_name]
        page_data = self._get_page_data(editor_data)

        info_label = QLabel(f"✂️ {editor_name}  ·  共 {len(editor_data)} 个视频")
        info_label.setObjectName("stats_label")
        layout.addWidget(info_label)

        table = self._create_data_table()
        self._fill_table(table, page_data)
        layout.addWidget(table)

        pagination = self._create_pagination_widget()
        layout.addWidget(pagination)

        return widget

    def _create_data_table(self) -> QTableWidget:
        headers = [
            "编号", "溯源码", "文件名", "剪辑", "运营", "入库日期",
            "总消耗", "本日消耗", "近7日消耗", "展现数", "点击数",
            "点击率", "转化数", "转化率", "千展数据", "3秒完播",
            "5秒完播", "评级"
        ]

        table = QTableWidget()
        table.setObjectName("assets_table")
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widths = [50, 100, 180, 80, 80, 100, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)

        return table

    def _fill_table(self, table: QTableWidget, data: list):
        row_count = len(data)
        col_count = table.columnCount()

        table.setRowCount(row_count)

        for row in range(row_count):
            for col in range(col_count):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QBrush(QColor(255, 255, 255)))
                table.setItem(row, col, item)

        rating_colors = {
            "S": QColor(16, 185, 129),
            "A": QColor(59, 130, 246),
            "B": QColor(251, 191, 36),
            "C": QColor(251, 146, 60),
            "D": QColor(239, 68, 68),
        }

        for row, record in enumerate(data):
            global_row = (self.current_page - 1) * self.page_size + row + 1

            # 提取数据（按正确的索引）
            trace_code = record[1] or "-"
            video_path = record[2] or ""
            record_date = record[3]
            editor_name = record[4] or "-"
            operator_name = record[5] or "-"

            file_name = video_path.split('/')[-1] if video_path else trace_code

            # 统计数据
            total_cost = record[6] if record[6] is not None else 0
            daily_cost = record[7] if record[7] is not None else 0
            week_cost = record[8] if record[8] is not None else 0
            impression = record[9] if record[9] is not None else 0
            clicks = record[10] if record[10] is not None else 0
            click_rate = record[11] if record[11] is not None else 0
            conversion = record[12] if record[12] is not None else 0
            conversion_rate = record[13] if record[13] is not None else 0
            cpm = record[14] if record[14] is not None else 0
            three_sec = record[15] if record[15] is not None else 0
            five_sec = record[16] if record[16] is not None else 0
            rating = record[17] if record[17] is not None else "B"

            values = [
                str(global_row),
                trace_code,
                file_name[:30] + "..." if len(file_name) > 30 else file_name,
                editor_name,
                operator_name,
                str(record_date)[:10] if record_date else "-",
                str(total_cost),
                str(daily_cost),
                str(week_cost),
                str(impression),
                str(clicks),
                f"{click_rate}%",
                str(conversion),
                f"{conversion_rate}%",
                str(cpm),
                f"{three_sec}%",
                f"{five_sec}%",
                rating,
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)

                if row % 2 == 0:
                    item.setBackground(QBrush(QColor(255, 255, 255)))
                else:
                    item.setBackground(QBrush(QColor(248, 249, 250)))

                if col == 17:
                    item.setBackground(QBrush(rating_colors.get(rating, QColor(200, 200, 200))))
                    item.setForeground(QBrush(QColor(255, 255, 255)))

                table.setItem(row, col, item)

        table.viewport().update()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_current_tab()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_current_tab()

    def _refresh_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            table = self.tab_widget.currentWidget().findChild(QTableWidget)
            if table:
                page_data = self._get_page_data(self.all_data)
                self._fill_table(table, page_data)
        else:
            editor_name = self.tab_widget.tabText(current_index).split('(')[0].strip()
            editor_data = [row for row in self.all_data if row[4] == editor_name]
            table = self.tab_widget.currentWidget().findChild(QTableWidget)
            if table:
                page_data = self._get_page_data(editor_data)
                self._fill_table(table, page_data)

        self._update_page_label()

    def _update_page_label(self):
        total = len(self.all_data)
        if total == 0:
            self.page_label.setText("第 0/0 页")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"第 {self.current_page}/{self.total_pages} 页")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

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

    def _get_today_count(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        count = sum(1 for row in self.all_data if row[3] and str(row[3])[:10] == today)
        return str(count)

    def _on_search(self, text: str):
        if not text.strip():
            self.current_page = 1
            self._rebuild_tabs()
            return

        filtered = []
        for row in self.all_data:
            file_name = row[2].split('/')[-1] if row[2] else row[1]
            operator = row[5] or ""
            editor = row[4] or ""
            if (text.lower() in file_name.lower() or
                    text.lower() in operator.lower() or
                    text.lower() in editor.lower()):
                filtered.append(row)

        self._filtered_data = filtered
        self.current_page = 1
        self.total_pages = max(1, (len(filtered) + self.page_size - 1) // self.page_size)
        self._rebuild_tabs_filtered()

    def _rebuild_tabs_filtered(self):
        self.tab_widget.clear()

        overview_tab = self._create_overview_tab_filtered()
        self.tab_widget.addTab(overview_tab, "总览")

        editor_groups = {}
        for row in self._filtered_data:
            editor_name = row[4] or "未知"
            if editor_name not in editor_groups:
                editor_groups[editor_name] = []
            editor_groups[editor_name].append(row)

        for editor_name, data in editor_groups.items():
            tab = self._create_editor_tab_with_data(editor_name, data)
            self.tab_widget.addTab(tab, f"{editor_name} ({len(data)})")

        self._update_page_label()

    def _create_overview_tab_filtered(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        total = len(self._filtered_data)
        label = QLabel(f"📋 搜索结果: {total} 条")
        label.setObjectName("stats_label")
        label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(label)

        table = self._create_data_table()
        page_data = self._get_page_data(self._filtered_data)
        self._fill_table(table, page_data)
        layout.addWidget(table)

        pagination = self._create_pagination_widget()
        layout.addWidget(pagination)

        return widget

    def _create_editor_tab_with_data(self, editor_name: str, data: list) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        info_label = QLabel(f"✂️ {editor_name}  ·  共 {len(data)} 个视频")
        info_label.setObjectName("stats_label")
        layout.addWidget(info_label)

        table = self._create_data_table()
        page_data = self._get_page_data(data)
        self._fill_table(table, page_data)
        layout.addWidget(table)

        pagination = self._create_pagination_widget()
        layout.addWidget(pagination)

        return widget

    def _on_import(self):
        QMessageBox.information(self, "导入", "导入功能开发中...")

    def _on_export(self):
        QMessageBox.information(self, "导出", "导出功能开发中...")