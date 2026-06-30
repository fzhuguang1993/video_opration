#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整数据流测试工具 - 飞书风格 + 复选框 + 排序（修复版）"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QLineEdit,
    QMessageBox, QHeaderView, QFrame, QMenu, QComboBox
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QBrush, QAction, QClipboard

import pymysql
from config import DB_CFG


# ============================================================
# 飞书配色方案
# ============================================================
class FeishuStyle:
    PRIMARY = "#3370FF"
    PRIMARY_HOVER = "#2B5FD6"
    PRIMARY_LIGHT = "#E8F0FE"
    SUCCESS = "#00B578"
    WARNING = "#FF8F1F"      # ← 加上
    DANGER = "#FF4D4F"       # ← 加上
    BG = "#F5F7FA"
    CARD_BG = "#FFFFFF"
    BORDER = "#E5E6EB"
    TEXT_PRIMARY = "#1D2129"
    TEXT_SECONDARY = "#86909C"
    TEXT_DISABLED = "#C9CDD4"  # ← 加上这一行
    TABLE_HEADER_BG = "#F7F8FA"
    TABLE_ROW_HOVER = "#F2F7FF"
    TABLE_ROW_ALT = "#FAFBFC"
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12
    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


def apply_feishu_style(app):
    app.setStyleSheet(f"""
        QWidget {{
            font-family: {FeishuStyle.FONT_FAMILY};
            font-size: 13px;
            color: {FeishuStyle.TEXT_PRIMARY};
            background-color: {FeishuStyle.BG};
        }}
        QMainWindow {{ background-color: {FeishuStyle.BG}; }}

        QFrame#card {{
            background-color: {FeishuStyle.CARD_BG};
            border-radius: {FeishuStyle.RADIUS_LG}px;
            border: 1px solid {FeishuStyle.BORDER};
        }}

        QLabel#title {{
            font-size: 20px;
            font-weight: 600;
            color: {FeishuStyle.TEXT_PRIMARY};
            letter-spacing: 0.3px;
        }}
        QLabel#subtitle {{
            font-size: 13px;
            color: {FeishuStyle.TEXT_SECONDARY};
            font-weight: 400;
        }}

        QPushButton {{
            border: none;
            border-radius: {FeishuStyle.RADIUS_SM}px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 500;
            background-color: {FeishuStyle.CARD_BG};
            color: {FeishuStyle.TEXT_PRIMARY};
            border: 1px solid {FeishuStyle.BORDER};
            min-height: 28px;
        }}
        QPushButton:hover {{
            background-color: {FeishuStyle.TABLE_ROW_HOVER};
            border-color: {FeishuStyle.PRIMARY};
        }}
        QPushButton#primary {{
            background-color: {FeishuStyle.PRIMARY};
            color: white;
            border: none;
        }}
        QPushButton#primary:hover {{ background-color: #2B5FD6; }}
        QPushButton#ghost {{
            background-color: transparent;
            border: none;
            color: {FeishuStyle.TEXT_SECONDARY};
        }}
        QPushButton#ghost:hover {{
            background-color: {FeishuStyle.TABLE_ROW_HOVER};
            color: {FeishuStyle.TEXT_PRIMARY};
        }}

        QLineEdit {{
            border: 1px solid {FeishuStyle.BORDER};
            border-radius: {FeishuStyle.RADIUS_SM}px;
            padding: 6px 12px;
            font-size: 13px;
            background-color: {FeishuStyle.CARD_BG};
            color: {FeishuStyle.TEXT_PRIMARY};
            min-height: 28px;
        }}
        QLineEdit:focus {{ border-color: {FeishuStyle.PRIMARY}; }}
        QLineEdit::placeholder {{ color: {FeishuStyle.TEXT_DISABLED}; }}

        QComboBox {{
            border: 1px solid {FeishuStyle.BORDER};
            border-radius: {FeishuStyle.RADIUS_SM}px;
            padding: 6px 12px;
            font-size: 13px;
            background-color: {FeishuStyle.CARD_BG};
            color: {FeishuStyle.TEXT_PRIMARY};
            min-height: 28px;
        }}
        QComboBox:hover {{ border-color: {FeishuStyle.PRIMARY}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {FeishuStyle.TEXT_SECONDARY};
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {FeishuStyle.BORDER};
            border-radius: {FeishuStyle.RADIUS_SM}px;
            background-color: {FeishuStyle.CARD_BG};
            selection-background-color: {FeishuStyle.PRIMARY_LIGHT};
            selection-color: {FeishuStyle.PRIMARY};
            padding: 4px 0;
        }}

        QTreeWidget {{
            background-color: {FeishuStyle.CARD_BG};
            border: 1px solid {FeishuStyle.BORDER};
            border-radius: {FeishuStyle.RADIUS_MD}px;
            outline: none;
            alternate-background-color: {FeishuStyle.TABLE_ROW_ALT};
            gridline-color: {FeishuStyle.BORDER};
            padding: 0px;
        }}
        QTreeWidget::item {{
            padding: 4px 2px;
            border: none;
        }}
        QTreeWidget::item:hover {{ background-color: {FeishuStyle.TABLE_ROW_HOVER}; }}
        QTreeWidget::item:selected {{
            background-color: {FeishuStyle.PRIMARY_LIGHT};
            color: {FeishuStyle.TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {FeishuStyle.TABLE_HEADER_BG};
            color: {FeishuStyle.TEXT_SECONDARY};
            font-size: 12px;
            font-weight: 500;
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {FeishuStyle.BORDER};
            text-align: left;
        }}
        QHeaderView::section:hover {{
            background-color: #EDEFF2;
        }}
        QHeaderView {{
            background-color: {FeishuStyle.TABLE_HEADER_BG};
            border: none;
            border-top-left-radius: {FeishuStyle.RADIUS_MD}px;
            border-top-right-radius: {FeishuStyle.RADIUS_MD}px;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            border-radius: 4px;
            margin: 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: {FeishuStyle.BORDER};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{ background: #C9CDD4; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

        QLabel#stats {{
            font-size: 13px;
            color: {FeishuStyle.TEXT_SECONDARY};
            padding: 4px 12px;
            background-color: {FeishuStyle.TABLE_HEADER_BG};
            border-radius: {FeishuStyle.RADIUS_SM}px;
        }}
        QLabel#detail {{
            font-size: 13px;
            color: {FeishuStyle.TEXT_SECONDARY};
        }}

        QWidget#toolbar {{
            background-color: {FeishuStyle.CARD_BG};
            border-radius: {FeishuStyle.RADIUS_MD}px;
            border: 1px solid {FeishuStyle.BORDER};
            padding: 8px 16px;
        }}
    """)


class FullDataTestWindow(QMainWindow):
    """完整数据流测试窗口"""

    # 列索引
    COL_CHECK = 0
    COL_TRACE_CODE = 1
    COL_FILE_NAME = 2
    COL_RECORD_DATE = 3
    COL_EDITOR = 4
    COL_OPERATOR = 5
    COL_TOTAL_COST = 6
    COL_COVER_IMPRESSION = 7
    COL_MATERIAL_IMPRESSION = 8
    COL_ACTION_COUNT = 9
    COL_COVER_CLICK_RATE = 10
    COL_IMPRESSION_1K_COST = 11
    COL_ACTION_RATE = 12
    COL_THREE_SEC_RATE = 13
    COL_FIVE_SEC_RATE = 14
    COL_END_RATE = 15
    COL_CONVERSION_COUNT = 16
    COL_CONVERSION_RATE = 17
    COL_RATING = 18
    COL_VIDEO_LINK = 19
    COL_COVER_LINK = 20
    COL_BIND_COUNT = 21

    HEADERS = [
        "",  # 复选框
        "溯源码", "文件名", "入库日期", "剪辑", "运营",
        "花费", "封面曝光", "素材曝光", "行为数",
        "封面点击率", "千展花费", "行为率",
        "3s播放率", "5s播放率", "完播率",
        "转化数", "转化率", "评级",
        "视频链接", "封面链接", "绑定数"
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据资产管理 · 测试工具")
        self.setGeometry(100, 100, 1600, 900)
        self._raw_data = []
        self._trace_lookup = {}
        self._all_data = []
        self._displayed_data = []
        self._user_cache = {}
        self._sort_column = -1
        self._sort_ascending = True
        self._context_menu_column = -1  # 右键菜单所在列
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 顶部标题
        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title = QLabel("数据资产管理")
        title.setObjectName("title")
        title_group.addWidget(title)
        subtitle = QLabel("video_trace ← JOIN video_stat ← video_bind 完整数据流")
        subtitle.setObjectName("subtitle")
        title_group.addWidget(subtitle)
        header.addLayout(title_group)
        header.addStretch()

        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_frame.setFixedHeight(36)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 4, 16, 4)
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {FeishuStyle.SUCCESS}; font-size: 14px;")
        status_layout.addWidget(self.status_dot)
        self.status_text = QLabel("数据已加载")
        self.status_text.setStyleSheet(f"color: {FeishuStyle.TEXT_SECONDARY}; font-size: 13px;")
        status_layout.addWidget(self.status_text)
        header.addWidget(status_frame)
        layout.addLayout(header)

        # 工具栏
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(12)

        # 搜索框
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"color: {FeishuStyle.TEXT_DISABLED}; padding: 6px 0 6px 12px;")
        search_layout.addWidget(search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索溯源码或文件名...")
        self.search_input.setStyleSheet("border: none; padding: 6px 12px;")
        self.search_input.textChanged.connect(self._filter_data)
        search_layout.addWidget(self.search_input)
        search_container.setStyleSheet(f"""
            QWidget {{
                background-color: {FeishuStyle.BG};
                border-radius: {FeishuStyle.RADIUS_SM}px;
                border: 1px solid {FeishuStyle.BORDER};
            }}
            QWidget:focus-within {{ border-color: {FeishuStyle.PRIMARY}; }}
        """)
        toolbar_layout.addWidget(search_container)

        # 过滤器
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "有视频链接", "有封面链接", "有子视频"])
        self.filter_combo.setFixedWidth(130)
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        toolbar_layout.addWidget(self.filter_combo)

        toolbar_layout.addStretch()

        # 批量操作按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("ghost")
        self.select_all_btn.setFixedWidth(60)
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.setObjectName("ghost")
        self.deselect_all_btn.setFixedWidth(80)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        toolbar_layout.addWidget(self.deselect_all_btn)

        self.copy_selected_btn = QPushButton("复制选中")
        self.copy_selected_btn.setObjectName("primary")
        self.copy_selected_btn.setFixedWidth(90)
        self.copy_selected_btn.clicked.connect(self._copy_selected_rows)
        toolbar_layout.addWidget(self.copy_selected_btn)

        toolbar_layout.addStretch()

        self.stats_label = QLabel("共 0 条数据")
        self.stats_label.setObjectName("stats")
        toolbar_layout.addWidget(self.stats_label)

        refresh_btn = QPushButton("刷新数据")
        refresh_btn.setObjectName("primary")
        refresh_btn.clicked.connect(self._load_data)
        toolbar_layout.addWidget(refresh_btn)

        layout.addWidget(toolbar)

        # 表格
        self.tree = QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True)
        self.tree.setMouseTracking(True)
        self.tree.setIndentation(20)

        # 右键菜单
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        # 双击复制 + 链接跳转
        self.tree.itemDoubleClicked.connect(self._on_item_double_click)

        # 表头点击排序
        self.tree.header().sectionClicked.connect(self._on_header_clicked)

        layout.addWidget(self.tree)

        # 底部
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        self.detail_label = QLabel("勾选行 · 双击复制 · 右键菜单 · 点击表头排序")
        self.detail_label.setObjectName("detail")
        bottom.addWidget(self.detail_label)
        bottom.addStretch()
        self.bottom_stats = QLabel("")
        self.bottom_stats.setObjectName("stats")
        bottom.addWidget(self.bottom_stats)
        layout.addLayout(bottom)

    def _get_user_name(self, user_id) -> str:
        if not user_id:
            return "-"
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            conn = pymysql.connect(**DB_CFG)
            cursor = conn.cursor()
            cursor.execute("SELECT real_name FROM sys_user WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                self._user_cache[user_id] = result[0]
                return result[0]
        except Exception as e:
            print(f"查询用户 {user_id} 失败: {e}")

        self._user_cache[user_id] = f"U{user_id}"
        return self._user_cache[user_id]

    def _get_table_columns(self, cursor, table: str) -> list:
        cursor.execute(f"DESCRIBE {table}")
        return [row[0] for row in cursor.fetchall()]

    def _load_data(self):
        try:
            self.status_text.setText("加载中...")
            self.status_dot.setStyleSheet(f"color: {FeishuStyle.WARNING}; font-size: 14px;")
            QApplication.processEvents()

            conn = pymysql.connect(**DB_CFG)
            cursor = conn.cursor()

            print("=" * 60)
            print("开始加载数据...")

            # Step 1: video_trace
            print("\n[Step 1] 查询 video_trace...")
            vt_columns = self._get_table_columns(cursor, 'video_trace')

            vt_select = []
            for col in ['id', 'trace_code', 'video_path', 'record_date', 'user_id', 'operator_id']:
                if col in vt_columns:
                    vt_select.append(f"vt.{col}")

            vt_sql = f"""
                SELECT {', '.join(vt_select)}
                FROM video_trace vt
                ORDER BY vt.record_date DESC
                LIMIT 200
            """
            cursor.execute(vt_sql)
            vt_rows = cursor.fetchall()
            print(f"  video_trace 共 {len(vt_rows)} 条")

            self._trace_lookup = {}
            for row in vt_rows:
                row_dict = {}
                for i, col in enumerate(['id', 'trace_code', 'video_path', 'record_date', 'user_id', 'operator_id']):
                    if col in vt_columns:
                        row_dict[col] = row[i] if i < len(row) else None
                self._trace_lookup[row_dict.get('trace_code', '')] = row_dict

            # Step 2: video_stat
            print("\n[Step 2] 查询 video_stat...")
            vs_columns = self._get_table_columns(cursor, 'video_stat')

            vs_select = []
            stat_cols = ['trace_code', 'total_cost', 'cover_impression', 'material_impression',
                         'action_count', 'cover_click', 'cover_click_rate', 'impression_1k_cost',
                         'click_1k_cost', 'photo_click_cost', 'action_cost', 'action_rate',
                         'conversion_count', 'conversion_rate', 'three_sec_rate', 'five_sec_rate',
                         'seventy_five_rate', 'end_rate', 'video_rating']
            if 'photo_url' in vs_columns:
                stat_cols.append('photo_url')
            if 'cover_url' in vs_columns:
                stat_cols.append('cover_url')
            if 'stat_date' in vs_columns:
                stat_cols.append('stat_date')

            for col in stat_cols:
                if col in vs_columns:
                    vs_select.append(col)

            vs_sql = f"SELECT {', '.join(vs_select)} FROM video_stat"
            cursor.execute(vs_sql)
            vs_rows = cursor.fetchall()
            print(f"  video_stat 共 {len(vs_rows)} 条")

            self.stat_map = {}
            for row in vs_rows:
                row_dict = {}
                for i, col in enumerate(vs_select):
                    row_dict[col] = row[i]
                self.stat_map[row_dict.get('trace_code', '')] = row_dict

            # Step 3: video_bind
            print("\n[Step 3] 查询 video_bind...")
            vb_columns = self._get_table_columns(cursor, 'video_bind')

            self.bind_map = {}
            self.child_codes = set()
            if 'bind_trace_code' in vb_columns and 'trace_code' in vb_columns:
                cursor.execute("SELECT bind_trace_code, trace_code FROM video_bind")
                bind_rows = cursor.fetchall()
                print(f"  video_bind 共 {len(bind_rows)} 条")
                for bind_tc, tc in bind_rows:
                    self.bind_map.setdefault(bind_tc, []).append(tc)
                    self.child_codes.add(tc)

            cursor.close()
            conn.close()

            # Step 4: 合并数据
            print("\n[Step 4] 合并数据...")
            self._all_data = []
            for tc, vt_info in self._trace_lookup.items():
                if tc in self.child_codes:
                    continue

                stat = self.stat_map.get(tc, {})

                editor_name = self._get_user_name(vt_info.get('user_id'))
                operator_name = self._get_user_name(vt_info.get('operator_id'))

                record = {
                    'trace_code': tc,
                    'video_path': vt_info.get('video_path', ''),
                    'record_date': vt_info.get('record_date'),
                    'editor_name': editor_name,
                    'operator_name': operator_name,
                    'user_id': vt_info.get('user_id'),
                    'operator_id': vt_info.get('operator_id'),
                    'is_host': tc in self.bind_map,
                    'children': self.bind_map.get(tc, []),
                    'total_cost': stat.get('total_cost', 0),
                    'cover_impression': stat.get('cover_impression', 0),
                    'material_impression': stat.get('material_impression', 0),
                    'action_count': stat.get('action_count', 0),
                    'cover_click': stat.get('cover_click', 0),
                    'cover_click_rate': stat.get('cover_click_rate', 0),
                    'impression_1k_cost': stat.get('impression_1k_cost', 0),
                    'click_1k_cost': stat.get('click_1k_cost', 0),
                    'photo_click_cost': stat.get('photo_click_cost', 0),
                    'action_cost': stat.get('action_cost', 0),
                    'action_rate': stat.get('action_rate', 0),
                    'conversion_count': stat.get('conversion_count', 0),
                    'conversion_rate': stat.get('conversion_rate', 0),
                    'three_sec_rate': stat.get('three_sec_rate', 0),
                    'five_sec_rate': stat.get('five_sec_rate', 0),
                    'seventy_five_rate': stat.get('seventy_five_rate', 0),
                    'end_rate': stat.get('end_rate', 0),
                    'video_rating': stat.get('video_rating', 'B') or 'B',
                    'photo_url': stat.get('photo_url', ''),
                    'cover_url': stat.get('cover_url', ''),
                    'stat_date': stat.get('stat_date'),
                }
                self._all_data.append(record)

            print(f"  合并后共 {len(self._all_data)} 条宿主数据")

            has_photo = sum(1 for r in self._all_data if r.get('photo_url') and str(r['photo_url']).strip())
            has_cover = sum(1 for r in self._all_data if r.get('cover_url') and str(r['cover_url']).strip())
            print(f"  有 photo_url: {has_photo} 条")
            print(f"  有 cover_url: {has_cover} 条")

            self._displayed_data = self._all_data.copy()
            self._display_data(self._displayed_data)
            self.stats_label.setText(
                f"共 {len(self._displayed_data)} 条 · 视频链接 {has_photo} 条 · 封面链接 {has_cover} 条")
            self.bottom_stats.setText(f"宿主视频 {len(self._all_data)} 个 · 绑定关系 {len(self.bind_map)} 组")

            self.status_text.setText("数据已加载")
            self.status_dot.setStyleSheet(f"color: {FeishuStyle.SUCCESS}; font-size: 14px;")

            print("\n数据加载完成!")
            print("=" * 60)

        except Exception as e:
            self.status_text.setText(f"加载失败: {str(e)[:30]}")
            self.status_dot.setStyleSheet(f"color: #FF4D4F; font-size: 14px;")
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _display_data(self, data):
        """显示数据到树形表格"""
        self.tree.setColumnCount(len(self.HEADERS))
        self.tree.setHeaderLabels(self.HEADERS)

        # 设置列宽 - 复选框列宽调大
        column_widths = {
            self.COL_CHECK: 45,  # 调大复选框列宽
            self.COL_TRACE_CODE: 90,
            self.COL_FILE_NAME: 160,
            self.COL_RECORD_DATE: 85,
            self.COL_EDITOR: 60,
            self.COL_OPERATOR: 60,
            self.COL_TOTAL_COST: 70,
            self.COL_COVER_IMPRESSION: 70,
            self.COL_MATERIAL_IMPRESSION: 70,
            self.COL_ACTION_COUNT: 55,
            self.COL_COVER_CLICK_RATE: 70,
            self.COL_IMPRESSION_1K_COST: 70,
            self.COL_ACTION_RATE: 60,
            self.COL_THREE_SEC_RATE: 55,
            self.COL_FIVE_SEC_RATE: 55,
            self.COL_END_RATE: 55,
            self.COL_CONVERSION_COUNT: 55,
            self.COL_CONVERSION_RATE: 55,
            self.COL_RATING: 40,
            self.COL_VIDEO_LINK: 100,
            self.COL_COVER_LINK: 100,
            self.COL_BIND_COUNT: 50,
        }
        for col, width in column_widths.items():
            self.tree.setColumnWidth(col, width)

        self.tree.header().setSectionResizeMode(self.COL_CHECK, QHeaderView.Fixed)

        self.tree.clear()

        for idx, record in enumerate(data):
            values = self._format_row(record, idx + 1, False)
            item = QTreeWidgetItem(values)

            # 启用复选框
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(self.COL_CHECK, Qt.Unchecked)

            # 存储完整数据
            item.setData(self.COL_TRACE_CODE, Qt.UserRole, record)

            # 存储 URL
            photo_url = record.get('photo_url', '')
            cover_url = record.get('cover_url', '')
            item.setData(self.COL_VIDEO_LINK, Qt.UserRole, photo_url or "")
            item.setData(self.COL_COVER_LINK, Qt.UserRole, cover_url or "")

            # 链接样式
            if photo_url and str(photo_url).strip():
                item.setText(self.COL_VIDEO_LINK, "视频链接")
                item.setForeground(self.COL_VIDEO_LINK, QBrush(QColor(FeishuStyle.PRIMARY)))
                font = item.font(self.COL_VIDEO_LINK)
                font.setUnderline(True)
                item.setFont(self.COL_VIDEO_LINK, font)
            else:
                item.setText(self.COL_VIDEO_LINK, "-")

            if cover_url and str(cover_url).strip():
                item.setText(self.COL_COVER_LINK, "封面链接")
                item.setForeground(self.COL_COVER_LINK, QBrush(QColor(FeishuStyle.SUCCESS)))
                font = item.font(self.COL_COVER_LINK)
                font.setUnderline(True)
                item.setFont(self.COL_COVER_LINK, font)
            else:
                item.setText(self.COL_COVER_LINK, "-")

            # 评级样式
            rating = record.get('video_rating', 'B') or 'B'
            rating_colors = {
                "S": QColor(16, 185, 129),
                "A": QColor(59, 130, 246),
                "B": QColor(251, 191, 36),
                "C": QColor(251, 146, 60),
                "D": QColor(239, 68, 68),
            }
            if rating in rating_colors:
                item.setBackground(self.COL_RATING, QBrush(rating_colors[rating]))
                if rating in ["S", "A", "D"]:
                    item.setForeground(self.COL_RATING, QBrush(QColor(255, 255, 255)))

            # 子视频
            if record.get('is_host') and record.get('children'):
                for child_tc in record['children']:
                    child_info = self._trace_lookup.get(child_tc)
                    if child_info:
                        child_stat = self.stat_map.get(child_tc, {})
                        child_record = {
                            'trace_code': child_tc,
                            'video_path': child_info.get('video_path', ''),
                            'record_date': child_info.get('record_date'),
                            'editor_name': '-',
                            'operator_name': '-',
                            'is_host': False,
                            'children': [],
                            'photo_url': child_stat.get('photo_url', ''),
                            'cover_url': child_stat.get('cover_url', ''),
                            'video_rating': child_stat.get('video_rating', 'B') or 'B',
                        }
                        c_values = self._format_row(child_record, idx + 1, True)
                        c_item = QTreeWidgetItem(c_values)
                        c_item.setFlags(c_item.flags() | Qt.ItemIsUserCheckable)
                        c_item.setCheckState(self.COL_CHECK, Qt.Unchecked)

                        c_item.setData(self.COL_TRACE_CODE, Qt.UserRole, child_record)

                        c_item.setData(self.COL_VIDEO_LINK, Qt.UserRole, child_record['photo_url'] or "")
                        c_item.setData(self.COL_COVER_LINK, Qt.UserRole, child_record['cover_url'] or "")

                        if child_record['photo_url']:
                            c_item.setText(self.COL_VIDEO_LINK, "视频链接")
                            c_item.setForeground(self.COL_VIDEO_LINK, QBrush(QColor(FeishuStyle.PRIMARY)))
                            font = c_item.font(self.COL_VIDEO_LINK)
                            font.setUnderline(True)
                            c_item.setFont(self.COL_VIDEO_LINK, font)
                        else:
                            c_item.setText(self.COL_VIDEO_LINK, "-")

                        if child_record['cover_url']:
                            c_item.setText(self.COL_COVER_LINK, "封面链接")
                            c_item.setForeground(self.COL_COVER_LINK, QBrush(QColor(FeishuStyle.SUCCESS)))
                            font = c_item.font(self.COL_COVER_LINK)
                            font.setUnderline(True)
                            c_item.setFont(self.COL_COVER_LINK, font)
                        else:
                            c_item.setText(self.COL_COVER_LINK, "-")

                        for c in range(c_item.columnCount()):
                            c_item.setBackground(c, QBrush(QColor("#F7F8FA")))

                        item.addChild(c_item)

            self.tree.addTopLevelItem(item)

        # 连接复选框变化事件
        self.tree.itemChanged.connect(self._on_item_changed)

        self._update_selection_stats()

    def _format_row(self, record, seq, is_child):
        photo_url = record.get('photo_url', '')
        cover_url = record.get('cover_url', '')

        return [
            "",
            record.get('trace_code', '-'),
            os.path.basename(record.get('video_path', '') or '') or record.get('trace_code', '-'),
            str(record.get('record_date', ''))[:10] if record.get('record_date') else '-',
            record.get('editor_name', '-'),
            record.get('operator_name', '-'),
            f"{record.get('total_cost', 0):.2f}",
            str(record.get('cover_impression', 0)),
            str(record.get('material_impression', 0)),
            str(record.get('action_count', 0)),
            f"{record.get('cover_click_rate', 0):.2f}%",
            f"{record.get('impression_1k_cost', 0):.2f}",
            f"{record.get('action_rate', 0):.4f}%",
            f"{record.get('three_sec_rate', 0):.2f}%",
            f"{record.get('five_sec_rate', 0):.2f}%",
            f"{record.get('end_rate', 0):.2f}%",
            str(record.get('conversion_count', 0)),
            f"{record.get('conversion_rate', 0):.2f}%",
            record.get('video_rating', 'B') or 'B',
            "视频链接" if photo_url else "-",
            "封面链接" if cover_url else "-",
            "子" if is_child else str(len(record.get('children', []))),
        ]

    # ============================================================
    # 复选框操作
    # ============================================================
    def _on_item_changed(self, item, column):
        if column == self.COL_CHECK:
            self._update_selection_stats()

    def _get_checked_items(self) -> list:
        checked = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(self.COL_CHECK) == Qt.Checked:
                checked.append(item)
        return checked

    def _select_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(self.COL_CHECK, Qt.Checked)
        self._update_selection_stats()

    def _deselect_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(self.COL_CHECK, Qt.Unchecked)
        self._update_selection_stats()

    def _update_selection_stats(self):
        checked = self._get_checked_items()
        self.bottom_stats.setText(
            f"共 {len(self._displayed_data)} 条 · 已选 {len(checked)} 条"
        )

    def _copy_selected_rows(self):
        checked = self._get_checked_items()
        if not checked:
            self.detail_label.setText("请先勾选要复制的行")
            return
        self._copy_rows(checked)

    # ============================================================
    # 表头排序
    # ============================================================
    def _on_header_clicked(self, column):
        if column == self.COL_CHECK:
            return

        if self._sort_column == column:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = column
            self._sort_ascending = True

        self.tree.header().setSortIndicatorShown(True)
        self.tree.header().setSortIndicator(
            column,
            Qt.AscendingOrder if self._sort_ascending else Qt.DescendingOrder
        )

        self._sort_data()

    def _sort_data(self):
        if self._sort_column < 0 or not self._displayed_data:
            return

        column = self._sort_column
        ascending = self._sort_ascending

        def get_sort_key(record):
            if column == self.COL_TRACE_CODE:
                return record.get('trace_code', '') or ''
            elif column == self.COL_FILE_NAME:
                return os.path.basename(record.get('video_path', '') or '') or ''
            elif column == self.COL_RECORD_DATE:
                return record.get('record_date', '') or ''
            elif column == self.COL_EDITOR:
                return record.get('editor_name', '') or ''
            elif column == self.COL_OPERATOR:
                return record.get('operator_name', '') or ''
            elif column in [self.COL_TOTAL_COST, self.COL_COVER_IMPRESSION,
                            self.COL_MATERIAL_IMPRESSION, self.COL_ACTION_COUNT,
                            self.COL_COVER_CLICK_RATE, self.COL_IMPRESSION_1K_COST,
                            self.COL_ACTION_RATE, self.COL_THREE_SEC_RATE,
                            self.COL_FIVE_SEC_RATE, self.COL_END_RATE,
                            self.COL_CONVERSION_COUNT, self.COL_CONVERSION_RATE]:
                return record.get(self._column_to_key(column), 0)
            elif column == self.COL_RATING:
                rating_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4}
                return rating_order.get(record.get('video_rating', 'B'), 2)
            elif column == self.COL_VIDEO_LINK:
                return 1 if record.get('photo_url') else 0
            elif column == self.COL_COVER_LINK:
                return 1 if record.get('cover_url') else 0
            elif column == self.COL_BIND_COUNT:
                return len(record.get('children', []))
            return ''

        self._displayed_data.sort(
            key=get_sort_key,
            reverse=not ascending
        )

        self._display_data(self._displayed_data)

    def _column_to_key(self, column):
        mapping = {
            self.COL_TOTAL_COST: 'total_cost',
            self.COL_COVER_IMPRESSION: 'cover_impression',
            self.COL_MATERIAL_IMPRESSION: 'material_impression',
            self.COL_ACTION_COUNT: 'action_count',
            self.COL_COVER_CLICK_RATE: 'cover_click_rate',
            self.COL_IMPRESSION_1K_COST: 'impression_1k_cost',
            self.COL_ACTION_RATE: 'action_rate',
            self.COL_THREE_SEC_RATE: 'three_sec_rate',
            self.COL_FIVE_SEC_RATE: 'five_sec_rate',
            self.COL_END_RATE: 'end_rate',
            self.COL_CONVERSION_COUNT: 'conversion_count',
            self.COL_CONVERSION_RATE: 'conversion_rate',
        }
        return mapping.get(column, '')

    # ============================================================
    # 搜索和过滤
    # ============================================================
    def _filter_data(self, text: str):
        if not text.strip():
            self._displayed_data = self._all_data.copy()
        else:
            filtered = []
            for r in self._all_data:
                if text.lower() in (r.get('trace_code', '') or "").lower():
                    filtered.append(r)
                elif text.lower() in (os.path.basename(r.get('video_path', '') or '') or "").lower():
                    filtered.append(r)
                elif text.lower() in (r.get('editor_name', '') or "").lower():
                    filtered.append(r)
                elif text.lower() in (r.get('operator_name', '') or "").lower():
                    filtered.append(r)
            self._displayed_data = filtered

        self._apply_filter(self.filter_combo.currentIndex(), from_search=True)
        self.stats_label.setText(f"共 {len(self._displayed_data)} 条数据 {'(过滤)' if text.strip() else ''}")

    def _apply_filter(self, index, from_search=False):
        if index == 0:
            if not from_search:
                self._displayed_data = self._all_data.copy()
        else:
            source_data = self._all_data
            filtered = []
            for r in source_data:
                if index == 1 and r.get('photo_url') and str(r['photo_url']).strip():
                    filtered.append(r)
                elif index == 2 and r.get('cover_url') and str(r['cover_url']).strip():
                    filtered.append(r)
                elif index == 3 and r.get('is_host') and r.get('children'):
                    filtered.append(r)
            self._displayed_data = filtered

        if self._sort_column >= 0:
            self._sort_data()
        else:
            self._display_data(self._displayed_data)

        self.stats_label.setText(f"共 {len(self._displayed_data)} 条数据")

    # ============================================================
    # 双击复制 + 链接跳转
    # ============================================================
    def _on_item_double_click(self, item, column):
        if column == self.COL_CHECK:
            return

        # 如果是链接列，打开链接
        if column in [self.COL_VIDEO_LINK, self.COL_COVER_LINK]:
            url = item.data(column, Qt.UserRole)
            if url and str(url).strip():
                self._open_url(url)
                return

        # 否则复制单元格
        text = item.text(column)
        if text and text != "-":
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.detail_label.setText(f"已复制: {text[:30]}{'...' if len(text) > 30 else ''}")

    # ============================================================
    # 右键菜单（纯文字，无 emoji）
    # ============================================================
    def _show_context_menu(self, pos: QPoint):
        tree = self.tree
        item = tree.itemAt(pos)

        if not item:
            return

        # 记录当前右键所在的列
        self._context_menu_column = tree.columnAt(pos.x())

        selected_items = tree.selectedItems()
        if not selected_items:
            selected_items = [item]

        column = self._context_menu_column
        column_name = self.HEADERS[column] if 0 <= column < len(self.HEADERS) else ""

        menu = QMenu(tree)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {FeishuStyle.CARD_BG};
                border: 1px solid {FeishuStyle.BORDER};
                border-radius: {FeishuStyle.RADIUS_SM}px;
                padding: 4px 0;
                min-width: 180px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {FeishuStyle.PRIMARY_LIGHT};
                color: {FeishuStyle.PRIMARY};
            }}
            QMenu::separator {{
                height: 1px;
                background: {FeishuStyle.BORDER};
                margin: 4px 8px;
            }}
        """)

        # ---- 全选 / 取消全选 ----
        select_all_action = QAction("全选", menu)
        select_all_action.triggered.connect(self._select_all)
        menu.addAction(select_all_action)

        deselect_all_action = QAction("取消全选", menu)
        deselect_all_action.triggered.connect(self._deselect_all)
        menu.addAction(deselect_all_action)

        menu.addSeparator()

        # ---- 复制 ----
        # 复制单行
        copy_row_action = QAction(f"复制行 (Tab分隔)", menu)
        copy_row_action.triggered.connect(lambda: self._copy_rows([item]))
        menu.addAction(copy_row_action)

        # 复制所有行
        copy_all_action = QAction(f"复制全部行 (Tab分隔)", menu)
        copy_all_action.triggered.connect(lambda: self._copy_rows(self._get_all_top_items()))
        menu.addAction(copy_all_action)

        menu.addSeparator()

        # ---- 排序（基于当前列） ----
        if column != self.COL_CHECK and column_name:
            sort_asc_action = QAction(f"升序排序 ({column_name})", menu)
            sort_asc_action.triggered.connect(lambda: self._sort_by_column(column, True))
            menu.addAction(sort_asc_action)

            sort_desc_action = QAction(f"降序排序 ({column_name})", menu)
            sort_desc_action.triggered.connect(lambda: self._sort_by_column(column, False))
            menu.addAction(sort_desc_action)

        menu.addSeparator()

        # ---- 刷新 ----
        refresh_action = QAction("刷新数据", menu)
        refresh_action.triggered.connect(self._load_data)
        menu.addAction(refresh_action)

        menu.exec(tree.viewport().mapToGlobal(pos))

    def _get_all_top_items(self) -> list:
        """获取所有顶层项"""
        items = []
        for i in range(self.tree.topLevelItemCount()):
            items.append(self.tree.topLevelItem(i))
        return items

    def _sort_by_column(self, column, ascending):
        """按指定列排序"""
        self._sort_column = column
        self._sort_ascending = ascending

        self.tree.header().setSortIndicatorShown(True)
        self.tree.header().setSortIndicator(
            column,
            Qt.AscendingOrder if ascending else Qt.DescendingOrder
        )

        self._sort_data()

    def _copy_cell(self, item, column):
        text = item.text(column)
        if text and text != "-":
            QApplication.clipboard().setText(text)
            self.detail_label.setText(f"已复制: {text[:30]}{'...' if len(text) > 30 else ''}")

    def _copy_rows(self, items):
        if not items:
            return

        rows_data = []
        for item in items:
            row_values = []
            for col in range(self.tree.columnCount()):
                if col == self.COL_CHECK:
                    continue
                text = item.text(col)
                # 如果是链接列，复制 URL 而不是显示文本
                if col in [self.COL_VIDEO_LINK, self.COL_COVER_LINK]:
                    url = item.data(col, Qt.UserRole)
                    if url and str(url).strip():
                        row_values.append(str(url))
                        continue
                row_values.append(text)
            rows_data.append("\t".join(row_values))

        text = "\n".join(rows_data)
        QApplication.clipboard().setText(text)
        self.detail_label.setText(f"已复制 {len(items)} 行 (可粘贴到 Excel)")

    def _copy_url(self, url):
        if url and str(url).strip():
            QApplication.clipboard().setText(str(url))
            self.detail_label.setText(f"已复制链接: {str(url)[:50]}{'...' if len(str(url)) > 50 else ''}")

    def _open_url(self, url):
        if not url or not str(url).strip():
            return
        import subprocess
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(url)])
            elif sys.platform == "win32":
                os.startfile(str(url))
            else:
                subprocess.Popen(["xdg-open", str(url)])
        except Exception:
            QApplication.clipboard().setText(str(url))
            QMessageBox.information(self, "提示", f"无法打开链接，已复制到剪贴板:\n{url}")


def main():
    app = QApplication(sys.argv)
    apply_feishu_style(app)
    window = FullDataTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()