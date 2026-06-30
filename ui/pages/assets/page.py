# ui/pages/assets/page.py
"""资产管理页面 - 主页面"""
import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTreeWidget, QPushButton, QLabel, QLineEdit, QMessageBox,
    QFrame, QProgressDialog, QApplication, QMenu,QTreeWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QBrush, QColor
from pathlib import Path
from config import ENV
from core.logger import get_logger
import pandas as pd
from .data_loader import AssetsDataLoader
from .tree_builder import TreeBuilder, FeishuStyle
from .date_selector import DateSelector


class AssetsPage(QWidget):
    """资产管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("assets_page")
        self.current_user = None
        self.user_role = 0
        self.user_id = None
        self.editors = []
        self.all_data = []
        self._filtered_data = []
        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1
        self._trace_lookup = {}
        self._current_tree = None
        self._current_builder = None
        self._current_data = []

        self._setup_ui()

        if ENV == "production":
            self._auto_timer = QTimer()
            self._auto_timer.timeout.connect(self._load_data)
            self._auto_timer.start(10 * 60 * 1000)

        self._update_last_update_time()

    # ================================================================
    # 权限
    # ================================================================
    def set_current_user(self, user_info: dict):
        self.current_user = user_info
        self.user_role = user_info.get("role", 0)
        self.user_id = user_info.get("user_id")
        self._apply_role_permissions()
        self._load_data()

    def _is_admin(self) -> bool:
        return self.user_role == 1

    def _apply_role_permissions(self):
        if hasattr(self, 'sync_btn'):
            self.sync_btn.setVisible(self._is_admin())

    # ================================================================
    # UI 构建
    # ================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        title_layout = QHBoxLayout()
        title = QLabel("📁 资产管理")
        title.setObjectName("page_title")
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.update_time_label = QLabel("上次更新: --")
        self.update_time_label.setStyleSheet("color: #8a8a9a; font-size: 12px;")
        title_layout.addWidget(self.update_time_label)
        layout.addLayout(title_layout)

        layout.addLayout(self._create_toolbar())

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("assets_tab_widget")
        loading = QWidget()
        loading_layout = QVBoxLayout(loading)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(QLabel("加载数据中..."))
        self.tab_widget.addTab(loading, "请先登录")
        layout.addWidget(self.tab_widget)

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

        self.date_selector = DateSelector()
        toolbar.addWidget(self.date_selector)

        toolbar.addSpacing(8)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setObjectName("ghost_btn")
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        self.sync_btn = QPushButton("📊 同步快手")
        self.sync_btn.setObjectName("success_btn")
        self.sync_btn.clicked.connect(self._on_sync_kuaishou)
        self.sync_btn.setVisible(False)
        toolbar.addWidget(self.sync_btn)

        return toolbar

    # ================================================================
    # 数据加载
    # ================================================================
    def _load_data(self):
        try:
            self.logger.info("加载资产管理数据...")
            self.current_page = 1

            loader = AssetsDataLoader(self.user_id, self.user_role)

            if loader.is_admin():
                self.editors = loader.load_editors()
            else:
                self.editors = []

            raw_data, all_binds = loader.load_raw_data()
            self._trace_lookup = loader.build_trace_lookup(raw_data)
            bind_map, child_codes = loader.build_bind_map(all_binds)
            self.all_data = loader.build_all_data(raw_data, child_codes, bind_map)

            self.total_pages = max(1, (len(self.all_data) + self.page_size - 1) // self.page_size)
            self._rebuild_tabs()
            self._update_last_update_time()
            self.logger.info(f"加载完成: {len(self.all_data)} 条, 角色={self.user_role}")

        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")

    # ================================================================
    # Tab 构建
    # ================================================================
    def _rebuild_tabs(self):
        self.tab_widget.clear()
        if self._is_admin():
            self.tab_widget.addTab(self._build_tab("总览", self.all_data, show_editor_count=True), "总览")
            for editor_id, editor_name in self.editors:
                editor_data = [r for r in self.all_data if r["editor_name"] == editor_name]
                count = len(editor_data)
                title = f"{editor_name} ({count})" if count > 0 else editor_name
                self.tab_widget.addTab(self._build_editor_tab(editor_data), title)
        else:
            self.tab_widget.addTab(self._build_tab("我的数据", self.all_data), f"我的数据 ({len(self.all_data)})")
        self._update_page_label()

    def _build_tab(self, title: str, data: list, show_editor_count: bool = False) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        host_count = sum(1 for d in data if d["is_host"])
        child_total = sum(len(d["children"]) for d in data)

        cards = [
            ("📹", "宿主/独立视频", str(len(data)), "#5e6ad2"),
            ("🔗", "有子视频", str(host_count), "#10b981"),
            ("📌", "绑定子视频", str(child_total), "#f59e0b"),
        ]
        if show_editor_count:
            cards.append(("✂️", "剪辑人员", str(len(self.editors)), "#8b5cf6"))
        cards.append(("📅", "今日新增", self._get_today_count(), "#ef4449"))

        card_layout = QHBoxLayout()
        card_layout.setSpacing(12)
        for icon, label, value, color in cards:
            card_layout.addWidget(self._create_stat_card(icon, label, value, color))
        card_layout.addStretch()
        layout.addLayout(card_layout)

        hint = QLabel("📋 视频列表（点击宿主视频可展开查看绑定子视频）")
        hint.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(hint)

        tree = self._create_and_fill_tree(data)
        layout.addWidget(tree)
        layout.addWidget(self._create_pagination())
        return widget

    def _build_editor_tab(self, data: list) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        editor_name = data[0]["editor_name"] if data else "未知"
        host_count = sum(1 for d in data if d["is_host"])
        child_total = sum(len(d["children"]) for d in data)
        info = QLabel(f"✂️ {editor_name}  ·  宿主/独立 {len(data)} 个  ·  🔗 有子视频 {host_count} 个  ·  📌 子视频 {child_total} 个")
        layout.addWidget(info)

        tree = self._create_and_fill_tree(data)
        layout.addWidget(tree)
        layout.addWidget(self._create_pagination())
        return widget

    def _build_search_tab(self, data: list) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        label = QLabel(f"📋 搜索结果: {len(data)} 条")
        label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(label)

        tree = self._create_and_fill_tree(data)
        layout.addWidget(tree)
        layout.addWidget(self._create_pagination())
        return widget

    # ================================================================
    # 树形控件
    # ================================================================
    def _create_and_fill_tree(self, data: list) -> QTreeWidget:
        builder = TreeBuilder(
            stat_map={},
            trace_lookup=self._trace_lookup,
            page_offset=(self.current_page - 1) * self.page_size
        )
        tree = builder.create_tree(
            on_double_click=self._on_item_double_click,
            on_context_menu=self._on_context_menu
        )
        self._current_tree = tree
        self._current_builder = builder
        self._current_data = data
        page_data = self._get_page_data(data)
        builder.fill_tree(tree, page_data)
        return tree

    def _on_item_double_click(self, item, column):
        """双击复制单元格内容"""
        if column == TreeBuilder.COL_CHECK:
            return
        text = item.text(column)
        if text and text != "-":
            QApplication.clipboard().setText(text)

    def _on_context_menu(self, pos):
        """右键菜单"""
        tree = self.sender()
        if not tree:
            return

        item = tree.itemAt(pos)
        if not item:
            return

        column = tree.columnAt(pos.x())
        menu = QMenu(tree)

        # 设置菜单样式
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

        # 获取 builder
        builder = getattr(tree, '_builder', None)
        if not builder:
            return

        # ---- 全选 / 取消全选 ----
        select_all_action = QAction("全选", tree)
        select_all_action.triggered.connect(builder.select_all)
        menu.addAction(select_all_action)

        deselect_all_action = QAction("取消全选", tree)
        deselect_all_action.triggered.connect(builder.deselect_all)
        menu.addAction(deselect_all_action)

        menu.addSeparator()

        # ---- 复制 ----
        copy_row_action = QAction("复制行 (Tab分隔)", tree)
        copy_row_action.triggered.connect(lambda: self._copy_rows_from_builder([item]))
        menu.addAction(copy_row_action)

        copy_all_action = QAction("复制全部行 (Tab分隔)", tree)
        copy_all_action.triggered.connect(self._copy_all_rows_from_builder)
        menu.addAction(copy_all_action)

        selected_count = builder.get_selected_count()
        if selected_count > 0:
            copy_selected_action = QAction(f"复制选中行 ({selected_count}行)", tree)
            copy_selected_action.triggered.connect(self._copy_selected_rows_from_builder)
            menu.addAction(copy_selected_action)

        # ---- 复制链接 ----
        if column in (TreeBuilder.COL_PHOTO_URL, TreeBuilder.COL_COVER_URL):
            url = item.data(column, Qt.UserRole)
            if url:
                label = "视频" if column == TreeBuilder.COL_PHOTO_URL else "封面"
                copy_link_action = QAction(f"复制{label}链接", tree)
                copy_link_action.triggered.connect(lambda: self._copy_url(url))
                menu.addAction(copy_link_action)

                open_link_action = QAction(f"打开{label}链接", tree)
                open_link_action.triggered.connect(lambda: self._open_url(url))
                menu.addAction(open_link_action)

            menu.addSeparator()

        # ---- 排序（基于当前列） ----
        if column != TreeBuilder.COL_CHECK:
            header_text = tree.headerItem().text(column)
            if header_text:
                sort_asc_action = QAction(f"升序排序 ({header_text})", tree)
                sort_asc_action.triggered.connect(lambda: self._sort_tree(column, True))
                menu.addAction(sort_asc_action)

                sort_desc_action = QAction(f"降序排序 ({header_text})", tree)
                sort_desc_action.triggered.connect(lambda: self._sort_tree(column, False))
                menu.addAction(sort_desc_action)

            menu.addSeparator()

        # ---- 刷新 ----
        refresh_action = QAction("刷新数据", tree)
        refresh_action.triggered.connect(self._load_data)
        menu.addAction(refresh_action)

        menu.exec_(tree.viewport().mapToGlobal(pos))

    # ================================================================
    # 复制辅助方法
    # ================================================================
    def _copy_rows_from_builder(self, items):
        builder = self._current_builder
        if not builder:
            return
        text = builder._format_rows_for_copy(items)
        if text:
            QApplication.clipboard().setText(text)

    def _copy_all_rows_from_builder(self):
        builder = self._current_builder
        if not builder:
            return
        text = builder.copy_all_rows()
        if text:
            QApplication.clipboard().setText(text)

    def _copy_selected_rows_from_builder(self):
        builder = self._current_builder
        if not builder:
            return
        text = builder.copy_selected_rows()
        if text:
            QApplication.clipboard().setText(text)

    def _copy_url(self, url):
        if url:
            QApplication.clipboard().setText(url)

    # ================================================================
    # 排序（page 层直接处理）
    # ================================================================
    # ui/pages/assets/page.py - 修复 _sort_tree 方法中的子项背景

    def _sort_tree(self, column, ascending):
        """在 page 层直接排序树 - 使用 pandas"""
        import pandas as pd

        print("=" * 60)
        print(f"🔍 _sort_tree 被调用: column={column}, ascending={ascending}")

        # 获取当前 Tab 的完整数据
        current_tab_widget = self.tab_widget.currentWidget()
        if not current_tab_widget:
            print("  ❌ 无法获取当前 Tab")
            return

        tab_index = self.tab_widget.currentIndex()
        tab_text = self.tab_widget.tabText(tab_index)
        print(f"  📋 当前 Tab: {tab_text}")

        # 根据 Tab 类型获取完整数据源
        if tab_text == "总览":
            full_data = self.all_data.copy()
        elif tab_text == "搜索结果" or tab_text.startswith("搜索结果"):
            full_data = self._filtered_data.copy()
        elif "(" in tab_text and tab_text != "总览":
            editor_name = tab_text.split('(')[0].strip()
            full_data = [r for r in self.all_data if r["editor_name"] == editor_name]
        else:
            full_data = self.all_data.copy()

        if not full_data:
            print("  ❌ full_data 为空，退出")
            return

        print(f"  ✅ 完整数据量: {len(full_data)}")

        # ✅ 关键修复：从 builder 获取 stat_map
        builder = self._current_builder
        stat_map = builder.stat_map if builder else {}
        print(f"  📊 stat_map 中有 {len(stat_map)} 条统计数据")

        # ✅ 将统计数据合并到 full_data 中
        enriched_data = []
        for record in full_data:
            trace_code = record.get('trace_code', '')
            stat = stat_map.get(trace_code, {})
            enriched_record = record.copy()
            enriched_record.update(stat)  # 合并统计字段
            enriched_data.append(enriched_record)

        if enriched_data:
            print(f"  📋 合并后第一条数据的 keys:")
            print(f"     {list(enriched_data[0].keys())}")

        # 列名映射
        from .tree_builder import TreeBuilder
        col_map = {
            TreeBuilder.COL_ID: 'id',
            TreeBuilder.COL_TRACE_CODE: 'trace_code',
            TreeBuilder.COL_FILE_NAME: 'video_path',
            TreeBuilder.COL_RECORD_DATE: 'record_date',
            TreeBuilder.COL_EDITOR: 'editor_name',
            TreeBuilder.COL_OPERATOR: 'operator_name',
            TreeBuilder.COL_TOTAL_COST: 'total_cost',
            TreeBuilder.COL_COVER_IMPRESSION: 'cover_impression',
            TreeBuilder.COL_MATERIAL_IMPRESSION: 'material_impression',
            TreeBuilder.COL_ACTION_COUNT: 'action_count',
            TreeBuilder.COL_COVER_CLICK_RATE: 'cover_click_rate',
            TreeBuilder.COL_IMPRESSION_1K_COST: 'impression_1k_cost',
            TreeBuilder.COL_CLICK_1K_COST: 'click_1k_cost',
            TreeBuilder.COL_ACTION_RATE: 'action_rate',
            TreeBuilder.COL_THREE_SEC_RATE: 'three_sec_rate',
            TreeBuilder.COL_FIVE_SEC_RATE: 'five_sec_rate',
            TreeBuilder.COL_SEVENTY_FIVE_RATE: 'seventy_five_rate',
            TreeBuilder.COL_END_RATE: 'end_rate',
            TreeBuilder.COL_CONVERSION_COUNT: 'conversion_count',
            TreeBuilder.COL_CONVERSION_RATE: 'conversion_rate',
            TreeBuilder.COL_RATING: 'video_rating',
            TreeBuilder.COL_PHOTO_URL: 'photo_url',
            TreeBuilder.COL_COVER_URL: 'cover_url',
            TreeBuilder.COL_BIND_COUNT: 'children',
        }

        sort_col = col_map.get(column, 'trace_code')
        print(f"  📊 排序列: {sort_col}")

        # 使用 pandas 排序
        df = pd.DataFrame(enriched_data)

        # 处理特殊列
        if column == TreeBuilder.COL_FILE_NAME:
            df['_sort_key'] = df['video_path'].apply(lambda x: os.path.basename(str(x)) if x else '')
            sort_col = '_sort_key'
        elif column == TreeBuilder.COL_BIND_COUNT:
            df['_sort_key'] = df['children'].apply(lambda x: len(x) if x else 0)
            sort_col = '_sort_key'
        elif column == TreeBuilder.COL_RATING:
            rating_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4}
            df['_sort_key'] = df['video_rating'].apply(lambda x: rating_order.get(x, 2))
            sort_col = '_sort_key'
        elif column in [TreeBuilder.COL_PHOTO_URL, TreeBuilder.COL_COVER_URL]:
            url_col = 'photo_url' if column == TreeBuilder.COL_PHOTO_URL else 'cover_url'
            df['_sort_key'] = df[url_col].apply(lambda x: 1 if x and str(x).strip() else 0)
            sort_col = '_sort_key'

        # 执行排序
        try:
            df_sorted = df.sort_values(by=sort_col, ascending=ascending, na_position='last')
        except KeyError as e:
            print(f"  ❌ 排序列 '{sort_col}' 不存在，使用 trace_code 排序")
            df_sorted = df.sort_values(by='trace_code', ascending=ascending, na_position='last')

        # 转回 dict 列表
        sorted_full_data = []
        for _, row in df_sorted.iterrows():
            record = row.to_dict()
            record.pop('_sort_key', None)
            sorted_full_data.append(record)

        print(f"  ✅ 排序完成，共 {len(sorted_full_data)} 条")

        # 更新 builder
        if builder:
            builder._source_data = sorted_full_data
            builder._displayed_data = sorted_full_data
            builder._sort_column = column
            builder._sort_ascending = ascending

        # 创建新的 TreeBuilder
        new_builder = TreeBuilder(
            stat_map=stat_map,
            trace_lookup=self._trace_lookup,
            page_offset=0
        )

        # 清理旧树
        old_tree = current_tab_widget.findChild(QTreeWidget)
        if old_tree:
            if hasattr(old_tree, '_link_handler'):
                try:
                    old_tree.viewport().removeEventFilter(old_tree._link_handler)
                    old_tree._link_handler.deleteLater()
                    old_tree._link_handler = None
                except Exception as e:
                    print(f"  ⚠️ 清理事件过滤器失败: {e}")

            layout = current_tab_widget.layout()
            if layout:
                layout.removeWidget(old_tree)
            old_tree.deleteLater()
            QApplication.processEvents()

        # 创建新 tree
        new_tree = new_builder.create_tree(
            on_double_click=self._on_item_double_click,
            on_context_menu=self._on_context_menu
        )

        # 填充全部排序后的数据
        new_builder.fill_tree(new_tree, sorted_full_data)

        # 将新 tree 添加到布局中
        layout = current_tab_widget.layout()
        if layout:
            pagination = current_tab_widget.findChild(QWidget, "pagination_widget")
            if pagination:
                layout.insertWidget(layout.indexOf(pagination), new_tree)
            else:
                layout.insertWidget(1, new_tree)

        # 更新引用
        self._current_tree = new_tree
        self._current_builder = new_builder
        self._current_data = sorted_full_data

        # 更新排序指示器
        new_tree.header().setSortIndicatorShown(True)
        new_tree.header().setSortIndicator(
            column,
            Qt.AscendingOrder if ascending else Qt.DescendingOrder
        )

        print(f"  ✅ 树重建完成，共 {new_tree.topLevelItemCount()} 个顶层项")
        print("=" * 60)

    def _open_url(self, url: str):
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", url], check=False)
            elif sys.platform == "win32":
                os.startfile(url)
            else:
                subprocess.run(["xdg-open", url], check=False)
        except Exception as e:
            self.logger.error(f"打开链接失败: {e}")

    # ================================================================
    # 分页
    # ================================================================
    def _get_page_data(self, data: list) -> list:
        start = (self.current_page - 1) * self.page_size
        return data[start:start + self.page_size]

    def _create_pagination(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("pagination_widget")  # ✅ 添加对象名，方便查找
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.setFixedWidth(80)
        self.prev_btn.clicked.connect(self._prev_page)

        self.page_label = QLabel("第 1/1 页")
        self.page_label.setFixedWidth(80)
        self.page_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.setFixedWidth(80)
        self.next_btn.clicked.connect(self._next_page)

        layout.addStretch()
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_btn)
        layout.addStretch()

        return widget

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_current_tab()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_current_tab()

    def _refresh_current_tab(self):
        idx = self.tab_widget.currentIndex()
        widget = self.tab_widget.currentWidget()
        tree = widget.findChild(QTreeWidget) if widget else None
        if not tree:
            return

        if self._is_admin() and idx == 0:
            data = self.all_data
        elif self._is_admin() and idx > 0:
            editor_name = self.tab_widget.tabText(idx).split('(')[0].strip()
            data = [r for r in self.all_data if r["editor_name"] == editor_name]
        else:
            data = self.all_data

        builder = TreeBuilder(
            stat_map={},
            trace_lookup=self._trace_lookup,
            page_offset=(self.current_page - 1) * self.page_size
        )
        builder.fill_tree(tree, self._get_page_data(data))
        self._current_builder = builder
        self._current_data = data
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

    # ================================================================
    # 搜索
    # ================================================================
    def _on_search(self, text: str):
        if not text.strip():
            self.current_page = 1
            self._rebuild_tabs()
            return

        self._filtered_data = [
            row for row in self.all_data
            if text.lower() in (
                Path(row["video_path"]).name if row["video_path"] else row["trace_code"]
            ).lower() or text.lower() in (row["operator_name"] or "").lower()
            or text.lower() in (row["editor_name"] or "").lower()
            or text.lower() in (row["trace_code"] or "").lower()
        ]

        self.current_page = 1
        self.total_pages = max(1, (len(self._filtered_data) + self.page_size - 1) // self.page_size)

        self.tab_widget.clear()
        self.tab_widget.addTab(self._build_search_tab(self._filtered_data), "搜索结果")

        if self._is_admin():
            groups = {}
            for row in self._filtered_data:
                groups.setdefault(row["editor_name"] or "未知", []).append(row)
            for name, data in groups.items():
                self.tab_widget.addTab(self._build_editor_tab(data), f"{name} ({len(data)})")

        self._update_page_label()

    # ================================================================
    # 同步快手
    # ================================================================
    def _on_sync_kuaishou(self):
        if not self._is_admin():
            QMessageBox.warning(self, "权限不足", "只有管理员才能同步快手数据")
            return

        progress = None
        try:
            from services.kuaishou_sync import sync_kuaishou_data

            start_date = self.date_selector.start_date
            end_date = self.date_selector.end_date

            progress = QProgressDialog(f"正在同步 {start_date} ~ {end_date} ...", "取消", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()

            result = sync_kuaishou_data(start_date=start_date, end_date=end_date)
            progress.close()

            QMessageBox.information(
                self, "同步完成",
                f"📅 日期范围: {start_date} ~ {end_date}\n"
                f"📊 同步结果:\n"
                f"  总数据: {result.get('total', 0)}\n"
                f"  有效数据: {result.get('clean', 0)}\n"
                f"  脏数据: {result.get('dirty', 0)}\n"
                f"  ✅ 已匹配: {result.get('matched', 0)}\n"
                f"  ❌ 待认领: {result.get('orphan', 0)}\n"
                f"  📝 更新记录: {result.get('report_updated', 0)}"
            )
            self._load_data()

        except Exception as e:
            if progress:
                progress.close()
            QMessageBox.critical(self, "同步失败", str(e))

    # ================================================================
    # 工具方法
    # ================================================================
    def _create_stat_card(self, icon: str, label: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat_card")
        card.setStyleSheet(f"""
            QFrame#stat_card {{
                background: white; border-radius: 8px; padding: 16px;
                min-height: 80px; border-left: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.addWidget(QLabel(f"{icon}  {label}"))
        layout.addWidget(QLabel(value))
        return card

    def _get_today_count(self) -> str:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        count = sum(1 for r in self.all_data if r["record_date"] and str(r["record_date"])[:10] == today)
        return str(count)

    def _update_last_update_time(self):
        from datetime import datetime
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.update_time_label.setText(f"上次更新: {time_str}")
        main_window = self.window()
        if main_window and hasattr(main_window, 'update_title_with_sync_time'):
            main_window.update_title_with_sync_time(time_str)