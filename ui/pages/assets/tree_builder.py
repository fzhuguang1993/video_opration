# ui/pages/assets/tree_builder.py
"""资产管理 - 树形控件构建（复用 test_video_stat.py 样式）"""
from pathlib import Path

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QApplication, QHeaderView
)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QColor, QBrush, QCursor

from .data_loader import AssetsDataLoader


# ============================================================
# 飞书配色方案（与 test_video_stat.py 保持一致）
# ============================================================
class FeishuStyle:
    PRIMARY = "#3370FF"
    PRIMARY_HOVER = "#2B5FD6"
    PRIMARY_LIGHT = "#E8F0FE"
    SUCCESS = "#00B578"
    WARNING = "#FF8F1F"
    DANGER = "#FF4D4F"
    BG = "#F5F7FA"
    CARD_BG = "#FFFFFF"
    BORDER = "#E5E6EB"
    TEXT_PRIMARY = "#1D2129"
    TEXT_SECONDARY = "#86909C"
    TEXT_DISABLED = "#C9CDD4"
    TABLE_HEADER_BG = "#F7F8FA"
    TABLE_ROW_HOVER = "#F2F7FF"
    TABLE_ROW_ALT = "#FAFBFC"
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12
    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


# ui/pages/assets/tree_builder.py - 修复 apply_tree_style 结尾
def apply_tree_style(tree: QTreeWidget):
    """应用飞书样式到树形表格（与 test_video_stat.py 一致）"""
    tree.setStyleSheet(f"""
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
            padding: 6px 4px;
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
        QScrollBar::handle:vertical:hover {{ background: {FeishuStyle.TEXT_DISABLED}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """)  # ✅ 这里加上闭合括号


class LinkClickHandler(QObject):
    """处理链接点击"""

    COL_PHOTO_URL = 22
    COL_COVER_URL = 23

    def __init__(self, tree: QTreeWidget):
        super().__init__(tree)
        self.tree = tree
        tree.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        # ✅ 增加安全检查：检查 tree 是否还有效
        if not self.tree:
            return False

        try:
            # 检查 tree 的 C++ 对象是否已被删除
            if self.tree is None:
                return False
            # 检查 viewport 是否还有效
            viewport = self.tree.viewport()
            if viewport is None:
                return False
            if obj != viewport:
                return False
        except RuntimeError:
            # C++ 对象已被删除，忽略事件
            return False

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            pos = event.pos()
            try:
                item = self.tree.itemAt(pos)
            except RuntimeError:
                return False
            if item:
                col = self.tree.columnAt(pos.x())
                if col in (self.COL_PHOTO_URL, self.COL_COVER_URL):
                    url = item.data(col, Qt.UserRole)
                    if url:
                        self._open_url(url)
                        self.tree.viewport().setCursor(QCursor(Qt.PointingHandCursor))
                        return True
            self.tree.viewport().setCursor(QCursor(Qt.ArrowCursor))
            return False

        if event.type() == QEvent.MouseMove:
            pos = event.pos()
            try:
                item = self.tree.itemAt(pos)
            except RuntimeError:
                return False
            if item:
                col = self.tree.columnAt(pos.x())
                if col in (self.COL_PHOTO_URL, self.COL_COVER_URL):
                    url = item.data(col, Qt.UserRole)
                    if url:
                        self.tree.viewport().setCursor(QCursor(Qt.PointingHandCursor))
                        return False
            self.tree.viewport().setCursor(QCursor(Qt.ArrowCursor))
            return False

        return False

    def _open_url(self, url: str):
        import sys
        import subprocess
        import os
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", url])
            elif sys.platform == "win32":
                os.startfile(url)
            else:
                subprocess.Popen(["xdg-open", url])
        except Exception:
            QApplication.clipboard().setText(url)


class TreeBuilder:
    """树形控件构建器"""

    # 列索引（第0列是复选框）
    COL_CHECK = 0
    COL_ID = 1
    COL_TRACE_CODE = 2
    COL_FILE_NAME = 3
    COL_RECORD_DATE = 4
    COL_EDITOR = 5
    COL_OPERATOR = 6
    COL_TOTAL_COST = 7
    COL_COVER_IMPRESSION = 8
    COL_MATERIAL_IMPRESSION = 9
    COL_ACTION_COUNT = 10
    COL_COVER_CLICK_RATE = 11
    COL_IMPRESSION_1K_COST = 12
    COL_CLICK_1K_COST = 13
    COL_ACTION_RATE = 14
    COL_THREE_SEC_RATE = 15
    COL_FIVE_SEC_RATE = 16
    COL_SEVENTY_FIVE_RATE = 17
    COL_END_RATE = 18
    COL_CONVERSION_COUNT = 19
    COL_CONVERSION_RATE = 20
    COL_RATING = 21
    COL_PHOTO_URL = 22
    COL_COVER_URL = 23
    COL_BIND_COUNT = 24

    HEADERS = [
        "",  # 复选框
        "编号", "溯源码", "文件名", "入库日期", "剪辑", "运营",
        "花费", "封面曝光", "素材曝光", "行为数",
        "封面点击率", "千展花费", "千次点击花费", "行为率",
        "3s播放", "5s播放", "75%播放", "完播率",
        "转化数", "转化率", "评级", "视频链接", "封面链接", "绑定数"
    ]

    # 列宽（与 test_video_stat.py 一致）
    COL_WIDTHS = {
        COL_CHECK: 45,
        COL_ID: 45,
        COL_TRACE_CODE: 90,
        COL_FILE_NAME: 160,
        COL_RECORD_DATE: 85,
        COL_EDITOR: 60,
        COL_OPERATOR: 60,
        COL_TOTAL_COST: 70,
        COL_COVER_IMPRESSION: 70,
        COL_MATERIAL_IMPRESSION: 70,
        COL_ACTION_COUNT: 55,
        COL_COVER_CLICK_RATE: 70,
        COL_IMPRESSION_1K_COST: 70,
        COL_CLICK_1K_COST: 80,
        COL_ACTION_RATE: 60,
        COL_THREE_SEC_RATE: 55,
        COL_FIVE_SEC_RATE: 55,
        COL_SEVENTY_FIVE_RATE: 55,
        COL_END_RATE: 55,
        COL_CONVERSION_COUNT: 55,
        COL_CONVERSION_RATE: 55,
        COL_RATING: 40,
        COL_PHOTO_URL: 100,
        COL_COVER_URL: 100,
        COL_BIND_COUNT: 50,
    }

    RATING_COLORS = {
        "S": QColor(16, 185, 129),
        "A": QColor(59, 130, 246),
        "B": QColor(251, 191, 36),
        "C": QColor(251, 146, 60),
        "D": QColor(239, 68, 68),
    }

    HOST_BG = QColor(255, 248, 240)
    CHILD_BG = QColor(248, 248, 250)

    def __init__(self, stat_map: dict, trace_lookup: dict, page_offset: int = 0):
        self.stat_map = stat_map
        self.trace_lookup = trace_lookup
        self.page_offset = page_offset
        self._tree = None
        self._sort_column = -1
        self._sort_ascending = True
        self._displayed_data = []
        self._source_data = []  # 保存原始数据用于排序
        self._on_selection_changed_callback = None

    def create_tree(self, on_double_click=None, on_context_menu=None) -> QTreeWidget:
        tree = QTreeWidget()
        self._tree = tree
        tree.setObjectName("assets_table")
        tree.setColumnCount(len(self.HEADERS))
        tree.setHeaderLabels(self.HEADERS)
        tree.setAlternatingRowColors(True)
        tree.setSelectionBehavior(QTreeWidget.SelectRows)
        tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        tree.setRootIsDecorated(True)
        tree.setItemsExpandable(True)
        tree.setMouseTracking(True)
        tree.viewport().setMouseTracking(True)
        tree.setIndentation(20)

        # 应用飞书样式
        apply_tree_style(tree)

        # 设置列宽
        for col, width in self.COL_WIDTHS.items():
            tree.setColumnWidth(col, width)
        tree.header().setSectionResizeMode(self.COL_CHECK, QHeaderView.Fixed)

        # 双击复制
        if on_double_click:
            tree.itemDoubleClicked.connect(on_double_click)

        # 右键菜单
        if on_context_menu:
            tree.setContextMenuPolicy(Qt.CustomContextMenu)
            tree.customContextMenuRequested.connect(on_context_menu)

        # 表头点击排序
        tree.header().sectionClicked.connect(self._on_header_clicked)

        # 复选框变化
        tree.itemChanged.connect(self._on_item_changed)

        # 链接处理器
        tree._link_handler = LinkClickHandler(tree)

        # 存储 builder 引用到 tree
        tree._builder = self

        return tree

    def fill_tree(self, tree: QTreeWidget, data: list):
        """填充树"""
        self._tree = tree
        self._displayed_data = data
        self._source_data = data.copy()  # 保存副本用于排序
        tree.clear()

        # 先收集统计数据
        self._collect_stat_codes(data)

        for idx, record in enumerate(data):
            seq = self.page_offset + idx + 1
            trace_code = record["trace_code"] or "-"
            values, photo_url, cover_url = self._format_row(trace_code, record, seq)

            item = QTreeWidgetItem(values)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(self.COL_CHECK, Qt.Unchecked)

            # 存储完整数据
            item.setData(self.COL_TRACE_CODE, Qt.UserRole, record)

            # 存储 URL
            item.setData(self.COL_PHOTO_URL, Qt.UserRole, photo_url or "")
            item.setData(self.COL_COVER_URL, Qt.UserRole, cover_url or "")

            # 链接样式
            if photo_url:
                item.setText(self.COL_PHOTO_URL, "视频链接")
                item.setForeground(self.COL_PHOTO_URL, QBrush(QColor(FeishuStyle.PRIMARY)))
                font = item.font(self.COL_PHOTO_URL)
                font.setUnderline(True)
                item.setFont(self.COL_PHOTO_URL, font)
            else:
                item.setText(self.COL_PHOTO_URL, "-")

            if cover_url:
                item.setText(self.COL_COVER_URL, "封面链接")
                item.setForeground(self.COL_COVER_URL, QBrush(QColor(FeishuStyle.SUCCESS)))
                font = item.font(self.COL_COVER_URL)
                font.setUnderline(True)
                item.setFont(self.COL_COVER_URL, font)
            else:
                item.setText(self.COL_COVER_URL, "-")

            # 评级样式
            rating = values[self.COL_RATING]
            if rating in self.RATING_COLORS:
                item.setBackground(self.COL_RATING, QBrush(self.RATING_COLORS[rating]))
                if rating in ["S", "A", "D"]:
                    item.setForeground(self.COL_RATING, QBrush(QColor(255, 255, 255)))

            # 宿主背景
            for c in range(item.columnCount()):
                if c != self.COL_CHECK:
                    item.setBackground(c, QBrush(self.HOST_BG))

            # 子视频
            if record["is_host"]:
                self._add_children(item, record)

            tree.addTopLevelItem(item)

        # 恢复排序指示器
        if self._sort_column >= 0:
            self._tree.header().setSortIndicatorShown(True)
            self._tree.header().setSortIndicator(
                self._sort_column,
                Qt.AscendingOrder if self._sort_ascending else Qt.DescendingOrder
            )

    # ============================================================
    # 复选框
    # ============================================================
    def _on_item_changed(self, item, column):
        if column == self.COL_CHECK and self._on_selection_changed_callback:
            self._on_selection_changed_callback()

    def set_selection_changed_callback(self, callback):
        self._on_selection_changed_callback = callback

    def get_checked_items(self) -> list:
        if not self._tree:
            return []
        checked = []
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.checkState(self.COL_CHECK) == Qt.Checked:
                checked.append(item)
        return checked

    def select_all(self):
        if not self._tree:
            return
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            item.setCheckState(self.COL_CHECK, Qt.Checked)

    def deselect_all(self):
        if not self._tree:
            return
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            item.setCheckState(self.COL_CHECK, Qt.Unchecked)

    def get_selected_count(self) -> int:
        return len(self.get_checked_items())

    def copy_selected_rows(self) -> str:
        checked = self.get_checked_items()
        if not checked:
            return ""
        return self._format_rows_for_copy(checked)

    def copy_all_rows(self) -> str:
        if not self._tree:
            return ""
        items = []
        for i in range(self._tree.topLevelItemCount()):
            items.append(self._tree.topLevelItem(i))
        return self._format_rows_for_copy(items)

    def copy_row(self, item) -> str:
        if not item:
            return ""
        return self._format_rows_for_copy([item])

    def _format_rows_for_copy(self, items: list) -> str:
        rows_data = []
        for item in items:
            row_values = []
            for col in range(self._tree.columnCount()):
                if col == self.COL_CHECK:
                    continue
                if col in [self.COL_PHOTO_URL, self.COL_COVER_URL]:
                    url = item.data(col, Qt.UserRole)
                    if url and str(url).strip():
                        row_values.append(str(url))
                        continue
                row_values.append(item.text(col))
            rows_data.append("\t".join(row_values))
        return "\n".join(rows_data)

    # ============================================================
    # 排序（修复版）
    # ============================================================
    def _on_header_clicked(self, column):
        """表头点击排序"""
        if column == self.COL_CHECK:
            return

        if self._sort_column == column:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = column
            self._sort_ascending = True

        self._apply_sort()

    def sort_by_column(self, column, ascending):
        """外部调用排序（右键菜单）"""
        self._sort_column = column
        self._sort_ascending = ascending
        self._apply_sort()

    def _apply_sort(self):
        """应用排序"""
        if self._sort_column < 0 or not self._source_data:
            return

        column = self._sort_column
        ascending = self._sort_ascending

        # 从原始数据排序
        sorted_data = self._source_data.copy()

        def get_sort_key(record):
            if column == self.COL_ID:
                return record.get('id', 0)
            elif column == self.COL_TRACE_CODE:
                return record.get('trace_code', '') or ''
            elif column == self.COL_FILE_NAME:
                return Path(record.get('video_path', '') or '').name or ''
            elif column == self.COL_RECORD_DATE:
                return record.get('record_date', '') or ''
            elif column == self.COL_EDITOR:
                return record.get('editor_name', '') or ''
            elif column == self.COL_OPERATOR:
                return record.get('operator_name', '') or ''
            elif column in [self.COL_TOTAL_COST, self.COL_COVER_IMPRESSION,
                           self.COL_MATERIAL_IMPRESSION, self.COL_ACTION_COUNT,
                           self.COL_COVER_CLICK_RATE, self.COL_IMPRESSION_1K_COST,
                           self.COL_CLICK_1K_COST, self.COL_ACTION_RATE,
                           self.COL_THREE_SEC_RATE, self.COL_FIVE_SEC_RATE,
                           self.COL_SEVENTY_FIVE_RATE, self.COL_END_RATE,
                           self.COL_CONVERSION_COUNT, self.COL_CONVERSION_RATE]:
                key_map = {
                    self.COL_TOTAL_COST: 'total_cost',
                    self.COL_COVER_IMPRESSION: 'cover_impression',
                    self.COL_MATERIAL_IMPRESSION: 'material_impression',
                    self.COL_ACTION_COUNT: 'action_count',
                    self.COL_COVER_CLICK_RATE: 'cover_click_rate',
                    self.COL_IMPRESSION_1K_COST: 'impression_1k_cost',
                    self.COL_CLICK_1K_COST: 'click_1k_cost',
                    self.COL_ACTION_RATE: 'action_rate',
                    self.COL_THREE_SEC_RATE: 'three_sec_rate',
                    self.COL_FIVE_SEC_RATE: 'five_sec_rate',
                    self.COL_SEVENTY_FIVE_RATE: 'seventy_five_rate',
                    self.COL_END_RATE: 'end_rate',
                    self.COL_CONVERSION_COUNT: 'conversion_count',
                    self.COL_CONVERSION_RATE: 'conversion_rate',
                }
                return record.get(key_map.get(column, ''), 0)
            elif column == self.COL_RATING:
                rating_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4}
                return rating_order.get(record.get('video_rating', 'B'), 2)
            elif column == self.COL_PHOTO_URL:
                return 1 if record.get('photo_url') else 0
            elif column == self.COL_COVER_URL:
                return 1 if record.get('cover_url') else 0
            elif column == self.COL_BIND_COUNT:
                return len(record.get('children', []))
            return ''

        sorted_data.sort(
            key=get_sort_key,
            reverse=not ascending
        )

        # 更新显示数据
        self._displayed_data = sorted_data

        # 重新填充树（不触发排序循环）
        self._fill_tree_without_sort(sorted_data)

        # 更新排序指示器
        if self._tree:
            self._tree.header().setSortIndicatorShown(True)
            self._tree.header().setSortIndicator(
                column,
                Qt.AscendingOrder if ascending else Qt.DescendingOrder
            )

    def _fill_tree_without_sort(self, data: list):
        """填充树但不触发排序（用于排序后刷新）"""
        if not self._tree:
            return

        tree = self._tree
        tree.clear()

        for idx, record in enumerate(data):
            seq = self.page_offset + idx + 1
            trace_code = record["trace_code"] or "-"
            values, photo_url, cover_url = self._format_row(trace_code, record, seq)

            item = QTreeWidgetItem(values)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(self.COL_CHECK, Qt.Unchecked)

            item.setData(self.COL_TRACE_CODE, Qt.UserRole, record)
            item.setData(self.COL_PHOTO_URL, Qt.UserRole, photo_url or "")
            item.setData(self.COL_COVER_URL, Qt.UserRole, cover_url or "")

            if photo_url:
                item.setText(self.COL_PHOTO_URL, "视频链接")
                item.setForeground(self.COL_PHOTO_URL, QBrush(QColor(FeishuStyle.PRIMARY)))
                font = item.font(self.COL_PHOTO_URL)
                font.setUnderline(True)
                item.setFont(self.COL_PHOTO_URL, font)
            else:
                item.setText(self.COL_PHOTO_URL, "-")

            if cover_url:
                item.setText(self.COL_COVER_URL, "封面链接")
                item.setForeground(self.COL_COVER_URL, QBrush(QColor(FeishuStyle.SUCCESS)))
                font = item.font(self.COL_COVER_URL)
                font.setUnderline(True)
                item.setFont(self.COL_COVER_URL, font)
            else:
                item.setText(self.COL_COVER_URL, "-")

            rating = values[self.COL_RATING]
            if rating in self.RATING_COLORS:
                item.setBackground(self.COL_RATING, QBrush(self.RATING_COLORS[rating]))
                if rating in ["S", "A", "D"]:
                    item.setForeground(self.COL_RATING, QBrush(QColor(255, 255, 255)))

            for c in range(item.columnCount()):
                if c != self.COL_CHECK:
                    item.setBackground(c, QBrush(self.HOST_BG))

            if record["is_host"]:
                self._add_children(item, record)

            tree.addTopLevelItem(item)

    # ============================================================
    # 数据加载
    # ============================================================
    def _collect_stat_codes(self, data: list):
        codes = [d["trace_code"] for d in data]
        for d in data:
            for child_tc in d.get("children", []):
                if child_tc not in codes:
                    codes.append(child_tc)
        self.stat_map = self.stat_map or {}
        if not codes:
            return
        loader = AssetsDataLoader()
        self.stat_map = loader.load_stat_data(codes)

    def _get_stat(self, trace_code: str) -> dict:
        return self.stat_map.get(trace_code, {})

    def _g(self, stat: dict, key: str, default=0):
        return stat.get(key, default) or default

    def _format_row(self, trace_code: str, record: dict, seq: int, is_child: bool = False):
        stat = self._get_stat(trace_code)
        g = lambda key, default=0: self._g(stat, key, default)

        file_name = Path(record.get("video_path", "") or "").name or trace_code
        photo_url = g("photo_url", "")
        cover_url = g("cover_url", "")

        values = [
            "",  # 复选框
            str(seq),
            trace_code,
            file_name[:30] + "..." if len(file_name) > 30 else file_name,
            str(record.get("record_date", ""))[:10] if record.get("record_date") else "-",
            record.get("editor_name", "-"),
            record.get("operator_name", "-"),
            f"{g('total_cost'):.2f}",
            str(g("cover_impression")),
            str(g("material_impression")),
            str(g("action_count")),
            f"{g('cover_click_rate'):.2f}%",
            f"{g('impression_1k_cost'):.2f}",
            f"{g('click_1k_cost'):.2f}",
            f"{g('action_rate'):.4f}%",
            f"{g('three_sec_rate'):.2f}%",
            f"{g('five_sec_rate'):.2f}%",
            f"{g('seventy_five_rate'):.2f}%",
            f"{g('end_rate'):.2f}%",
            str(g("conversion_count")),
            f"{g('conversion_rate'):.2f}%",
            g("video_rating", "B") or "B",
            "视频链接" if photo_url else "-",
            "封面链接" if cover_url else "-",
            "子" if is_child else str(len(record.get("children", []))),
        ]
        return values, photo_url, cover_url

    def _add_children(self, parent_item: QTreeWidgetItem, record: dict):
        for child_seq, child_tc in enumerate(record["children"], 1):
            child_info = self.trace_lookup.get(child_tc)
            if not child_info:
                continue
            c_values, c_photo_url, c_cover_url = self._format_row(child_tc, child_info, child_seq, is_child=True)
            c_item = QTreeWidgetItem(c_values)
            c_item.setFlags(c_item.flags() | Qt.ItemIsUserCheckable)
            c_item.setCheckState(self.COL_CHECK, Qt.Unchecked)

            c_item.setData(self.COL_TRACE_CODE, Qt.UserRole, child_info)
            c_item.setData(self.COL_PHOTO_URL, Qt.UserRole, c_photo_url or "")
            c_item.setData(self.COL_COVER_URL, Qt.UserRole, c_cover_url or "")

            if c_photo_url:
                c_item.setText(self.COL_PHOTO_URL, "视频链接")
                c_item.setForeground(self.COL_PHOTO_URL, QBrush(QColor(FeishuStyle.PRIMARY)))
                font = c_item.font(self.COL_PHOTO_URL)
                font.setUnderline(True)
                c_item.setFont(self.COL_PHOTO_URL, font)
            else:
                c_item.setText(self.COL_PHOTO_URL, "-")

            if c_cover_url:
                c_item.setText(self.COL_COVER_URL, "封面链接")
                c_item.setForeground(self.COL_COVER_URL, QBrush(QColor(FeishuStyle.SUCCESS)))
                font = c_item.font(self.COL_COVER_URL)
                font.setUnderline(True)
                c_item.setFont(self.COL_COVER_URL, font)
            else:
                c_item.setText(self.COL_COVER_URL, "-")

            for c in range(c_item.columnCount()):
                if c != self.COL_CHECK:
                    c_item.setBackground(c, QBrush(self.CHILD_BG))

            parent_item.addChild(c_item)