# utils/tools/trace/view.py
"""视频溯源工具视图"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox, QLineEdit,
    QFileDialog, QMessageBox, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPlainTextEdit, QCheckBox, QFrame, QTreeWidget, QTreeWidgetItem,
    QMenu, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QColor, QBrush

from .widget import TraceDropArea
from .worker import TraceWorker, BindWorker


class TraceView(QWidget):
    """视频溯源视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_files = []
        self.current_user = None
        self.operators = []
        self.worker = None
        self._setup_ui()
        self._load_operators()

    def set_user(self, user_info: dict):
        self.current_user = user_info
        self._refresh_bind_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        tab_widget = QTabWidget()
        tab_widget.setObjectName("trace_tab_widget")

        tab_widget.addTab(self._create_trace_tab(), "溯源格式化")
        tab_widget.addTab(self._create_bind_tab(), "视频绑定")

        main_layout.addWidget(tab_widget)

    # ================================================================
    # Tab 1: 溯源格式化
    # ================================================================
    def _create_trace_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        video_group = QGroupBox("视频源")
        video_layout = QVBoxLayout(video_group)
        video_layout.setSpacing(4)

        self.video_drop = TraceDropArea("拖拽视频或文件夹到此", min_height=70)
        self.video_drop.files_dropped.connect(self._on_video_dropped)
        video_layout.addWidget(self.video_drop)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        select_folder_btn = QPushButton("选择文件夹")
        select_folder_btn.clicked.connect(self._select_video_folder)
        btn_row.addWidget(select_folder_btn)

        select_files_btn = QPushButton("选择文件")
        select_files_btn.clicked.connect(self._select_video_files)
        btn_row.addWidget(select_files_btn)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear_video_list)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        video_layout.addLayout(btn_row)

        self.video_count_label = QLabel("共 0 个视频")
        self.video_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        video_layout.addWidget(self.video_count_label)

        layout.addWidget(video_group)

        param_row = QHBoxLayout()
        param_row.setSpacing(16)

        operator_group = QGroupBox("运营信息")
        operator_layout = QVBoxLayout(operator_group)
        operator_layout.setSpacing(8)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("运营人员:"))
        self.operator_combo = QComboBox()
        self.operator_combo.setFixedWidth(140)
        op_row.addWidget(self.operator_combo)
        op_row.addStretch()
        operator_layout.addLayout(op_row)

        editor_row = QHBoxLayout()
        editor_row.addWidget(QLabel("剪辑人员:"))
        self.editor_label = QLabel("（当前登录用户）")
        self.editor_label.setStyleSheet("color: #5e6ad2; font-weight: 500;")
        editor_row.addWidget(self.editor_label)
        editor_row.addStretch()
        operator_layout.addLayout(editor_row)

        operator_layout.addStretch()
        param_row.addWidget(operator_group, 1)

        smb_group = QGroupBox("SMB 上传")
        smb_layout = QVBoxLayout(smb_group)
        smb_layout.setSpacing(8)

        self.smb_enabled = QCheckBox("处理完成后上传到 SMB")
        self.smb_enabled.setChecked(True)
        smb_layout.addWidget(self.smb_enabled)

        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("子目录:"))
        self.smb_subpath = QLineEdit()
        self.smb_subpath.setPlaceholderText("留空则使用默认路径（如: 剪辑名/日期）")
        sub_row.addWidget(self.smb_subpath)
        smb_layout.addLayout(sub_row)

        self.smb_auto_subpath = QCheckBox("自动生成子目录（剪辑名/日期）")
        self.smb_auto_subpath.setChecked(True)
        smb_layout.addWidget(self.smb_auto_subpath)

        smb_layout.addStretch()
        param_row.addWidget(smb_group, 1)

        layout.addLayout(param_row)

        preview_group = QGroupBox("处理日志")
        preview_layout = QVBoxLayout(preview_group)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QPlainTextEdit {
                font-family: "Menlo", "Consolas", monospace;
                font-size: 11px;
                background: #fafafa;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        preview_layout.addWidget(self.log_text)
        layout.addWidget(preview_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("执行溯源格式化")
        self.execute_btn.setObjectName("primary_btn")
        self.execute_btn.clicked.connect(self._execute_trace)
        btn_layout.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_trace)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    # ================================================================
    # Tab 2: 视频绑定（列表 + 右键 + 可展开）
    # ================================================================
    def _create_bind_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        tip = QLabel(
            "使用说明: 右键视频可复制溯源码，复制后右键另一条视频选择「绑定到此」即可将翻拍版绑定到母版。"
            "已绑定的母版会显示子视频数量，点击左侧箭头可展开查看。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet(
            "color: #6b7280; font-size: 12px; padding: 8px; "
            "background: #f0f9ff; border-radius: 6px; border: 1px solid #bae6fd;"
        )
        layout.addWidget(tip)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("搜索:"))
        self.bind_search_input = QLineEdit()
        self.bind_search_input.setPlaceholderText("输入溯源码或文件名搜索...")
        self.bind_search_input.setFixedWidth(220)
        self.bind_search_input.textChanged.connect(self._on_bind_search_changed)
        search_row.addWidget(self.bind_search_input)

        self.bind_show_all_cb = QCheckBox("显示全部（含子视频）")
        self.bind_show_all_cb.toggled.connect(self._refresh_bind_list)
        search_row.addWidget(self.bind_show_all_cb)

        search_row.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_bind_list)
        search_row.addWidget(refresh_btn)

        layout.addLayout(search_row)

        self.bind_tree = QTreeWidget()
        self.bind_tree.setColumnCount(5)
        self.bind_tree.setHeaderLabels(["溯源码", "文件名", "日期", "剪辑", "绑定数"])
        self.bind_tree.setRootIsDecorated(True)
        self.bind_tree.setAlternatingRowColors(True)
        self.bind_tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.bind_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.bind_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bind_tree.customContextMenuRequested.connect(self._show_bind_context_menu)
        self.bind_tree.itemDoubleClicked.connect(self._on_bind_tree_double_click)

        header = self.bind_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.bind_tree.setStyleSheet("""
            QTreeWidget {
                background: #ffffff;
                border: 1px solid #e6e7ea;
                border-radius: 8px;
                gridline-color: #f1f2f4;
                alternate-background-color: #fafafb;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px 8px;
                border: none;
            }
            QTreeWidget::item:hover {
                background: #f1f2f4;
            }
            QTreeWidget::item:selected {
                background: #ebecef;
                color: #1a1a2e;
            }
            QHeaderView::section {
                background: #f5f6f8;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid #e6e7ea;
                font-weight: 600;
                color: #4a4a5a;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.bind_tree, 1)

        page_row = QHBoxLayout()
        self.bind_prev_btn = QPushButton("上一页")
        self.bind_prev_btn.setObjectName("ghost_btn")
        self.bind_prev_btn.clicked.connect(self._bind_prev_page)
        page_row.addWidget(self.bind_prev_btn)

        self.bind_page_label = QLabel("第 0/0 页")
        self.bind_page_label.setAlignment(Qt.AlignCenter)
        self.bind_page_label.setFixedWidth(120)
        page_row.addWidget(self.bind_page_label)

        self.bind_next_btn = QPushButton("下一页")
        self.bind_next_btn.setObjectName("ghost_btn")
        self.bind_next_btn.clicked.connect(self._bind_next_page)
        page_row.addWidget(self.bind_next_btn)

        page_row.addStretch()

        self.bind_info_label = QLabel("共 0 条")
        self.bind_info_label.setAlignment(Qt.AlignRight)
        page_row.addWidget(self.bind_info_label)

        layout.addLayout(page_row)

        self._bind_all_data = []
        self._bind_map = {}
        self._trace_lookup = {}
        self._bind_page = 0
        self._bind_page_size = 20

        return widget

    # ================================================================
    # 数据加载
    # ================================================================
    def _load_operators(self):
        import pymysql
        from config import DB_CFG
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT id, real_name FROM sys_user WHERE role = 2 ORDER BY real_name")
            self.operators = cur.fetchall()
            cur.close()
            conn.close()

            self.operator_combo.clear()
            for uid, name in self.operators:
                self.operator_combo.addItem(name, uid)
        except Exception as e:
            self._log(f"加载运营列表失败: {e}")

    # ================================================================
    # 视频源操作
    # ================================================================
    def _on_video_dropped(self, files: list, folders: list):
        for folder in folders:
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        self.video_files.append(os.path.join(root, f))
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                if file not in self.video_files:
                    self.video_files.append(file)
        self._update_video_count()

    def _select_video_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder:
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        self.video_files.append(os.path.join(root, f))
            self._update_video_count()

    def _select_video_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv)"
        )
        for path in paths:
            if path not in self.video_files:
                self.video_files.append(path)
        self._update_video_count()

    def _clear_video_list(self):
        self.video_files = []
        self._update_video_count()

    def _update_video_count(self):
        self.video_count_label.setText(f"共 {len(self.video_files)} 个视频")

    # ================================================================
    # 溯源执行
    # ================================================================
    def _execute_trace(self):
        if not self.video_files:
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return

        if self.operator_combo.count() == 0:
            QMessageBox.warning(self, "提示", "没有可用的运营人员，请联系管理员")
            return

        operator_idx = self.operator_combo.currentIndex()
        operator_id = self.operator_combo.itemData(operator_idx)
        operator_name = self.operator_combo.currentText()

        upload_to_smb = self.smb_enabled.isChecked()
        auto_subpath = self.smb_auto_subpath.isChecked()
        custom_subpath = self.smb_subpath.text().strip()

        self.log_text.clear()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.execute_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.worker = TraceWorker(
            video_paths=self.video_files,
            operator_id=operator_id,
            operator_name=operator_name,
            upload_to_smb=upload_to_smb,
            auto_subpath=auto_subpath,
            custom_subpath=custom_subpath
        )
        self.worker.progress.connect(self._on_trace_progress)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._on_trace_finished)
        self.worker.start()

    def _cancel_trace(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._log("正在取消...")

    def _on_trace_progress(self, current: int, total: int, name: str):
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))

    def _on_trace_finished(self, success: bool, msg: str):
        self.progress_bar.setValue(100 if success else 0)
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._log(f"\n{msg}")
        QMessageBox.information(self, "处理完成", msg)

        # ... existing code ...
        # ================================================================
        # Tab2: 绑定列表 - 数据加载与显示
        # ================================================================
    def _refresh_bind_list(self):
        import pymysql
        from config import DB_CFG
        from pathlib import Path

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            user_role = self.current_user.get("role", 0) if self.current_user else 0
            user_id = self.current_user.get("user_id") if self.current_user else None

            where = ""
            params = []
            if user_role == 3:
                where = "WHERE vt.user_id = %s"
                params.append(user_id)

            cur.execute(f"""
                SELECT vt.trace_code, vt.video_path, vt.record_date, 
                       su.real_name, vt.user_id
                FROM video_trace vt
                LEFT JOIN sys_user su ON vt.user_id = su.id
                {where}
                ORDER BY vt.record_date DESC, vt.trace_code ASC
            """, params)
            all_traces = cur.fetchall()

            cur.execute("SELECT trace_code, bind_trace_code, user_id, bind_time FROM video_bind")
            all_binds = cur.fetchall()

            cur.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")
            return

        self._bind_map = {}
        child_codes = set()
        for row in all_binds:
            child_code, parent_code, bind_uid, bind_time = row
            if parent_code not in self._bind_map:
                self._bind_map[parent_code] = []
            self._bind_map[parent_code].append({
                "trace_code": child_code,
                "user_id": bind_uid,
                "bind_time": bind_time
            })
            child_codes.add(child_code)

        self._trace_lookup = {}
        for row in all_traces:
            self._trace_lookup[row[0]] = {
                "trace_code": row[0],
                "video_path": row[1],
                "filename": Path(row[1]).name if row[1] else "",
                "record_date": str(row[2]),
                "editor_name": row[3] or "",
            }

        show_all = self.bind_show_all_cb.isChecked()

        self._bind_all_data = []
        for row in all_traces:
            tc = row[0]
            is_child = tc in child_codes
            is_host = tc in self._bind_map

            if show_all:
                self._bind_all_data.append({
                    "trace_code": tc,
                    "video_path": row[1],
                    "filename": Path(row[1]).name if row[1] else "",
                    "record_date": str(row[2]),
                    "editor_name": row[3] or "",
                    "is_host": is_host,
                    "is_child": is_child,
                    "children": self._bind_map.get(tc, [])
                })
            else:
                if not is_child:
                    self._bind_all_data.append({
                        "trace_code": tc,
                        "video_path": row[1],
                        "filename": Path(row[1]).name if row[1] else "",
                        "record_date": str(row[2]),
                        "editor_name": row[3] or "",
                        "is_host": is_host,
                        "is_child": False,
                        "children": self._bind_map.get(tc, [])
                    })

        self._bind_page = 0
        self._display_bind_page()

    def _on_bind_search_changed(self, text: str):
        self._bind_page = 0
        self._display_bind_page()

    def _get_filtered_bind_data(self):
        keyword = self.bind_search_input.text().strip().lower()
        if not keyword:
            return self._bind_all_data
        return [
            item for item in self._bind_all_data
            if keyword in item["trace_code"].lower() or keyword in item["filename"].lower()
        ]

    def _display_bind_page(self):
        filtered = self._get_filtered_bind_data()
        total = len(filtered)
        total_pages = max(1, (total + self._bind_page_size - 1) // self._bind_page_size)

        if self._bind_page >= total_pages:
            self._bind_page = total_pages - 1
        if self._bind_page < 0:
            self._bind_page = 0

        start = self._bind_page * self._bind_page_size
        end = min(start + self._bind_page_size, total)
        page_data = filtered[start:end]

        self.bind_tree.clear()

        for item in page_data:
            child_count = len(item["children"])
            bind_label = str(child_count) if item["is_host"] else "-"

            tree_item = QTreeWidgetItem([
                item["trace_code"],
                item["filename"],
                item["record_date"],
                item["editor_name"],
                bind_label
            ])

            if item["is_host"]:
                tree_item.setData(0, Qt.UserRole, {
                    "type": "host",
                    "trace_code": item["trace_code"],
                    "children": item["children"]
                })
                font = tree_item.font(0)
                font.setBold(True)
                for c in range(5):
                    tree_item.setFont(c, font)
                    tree_item.setForeground(c, QBrush(QColor("#5e6ad2")))

                for child in item["children"]:
                    child_tc = child["trace_code"]
                    child_info = self._trace_lookup.get(child_tc)
                    child_filename = child_info["filename"] if child_info else "(未知)"
                    child_date = child_info["record_date"] if child_info else ""
                    child_editor = child_info["editor_name"] if child_info else ""

                    child_item = QTreeWidgetItem([
                        child_tc,
                        child_filename,
                        child_date,
                        child_editor,
                        "子"
                    ])
                    child_item.setData(0, Qt.UserRole, {
                        "type": "child",
                        "trace_code": child_tc,
                        "parent_code": item["trace_code"]
                    })
                    for c in range(5):
                        child_item.setForeground(c, QBrush(QColor("#8a8a9a")))
                    tree_item.addChild(child_item)

            else:
                tree_item.setData(0, Qt.UserRole, {
                    "type": "standalone",
                    "trace_code": item["trace_code"]
                })

            self.bind_tree.addTopLevelItem(tree_item)

        self.bind_page_label.setText(f"第 {self._bind_page + 1}/{total_pages} 页")
        self.bind_info_label.setText(f"共 {total} 条")
        self.bind_prev_btn.setEnabled(self._bind_page > 0)
        self.bind_next_btn.setEnabled(self._bind_page < total_pages - 1)

    def _bind_prev_page(self):
        if self._bind_page > 0:
            self._bind_page -= 1
            self._display_bind_page()

    def _bind_next_page(self):
        filtered = self._get_filtered_bind_data()
        total_pages = max(1, (len(filtered) + self._bind_page_size - 1) // self._bind_page_size)
        if self._bind_page < total_pages - 1:
            self._bind_page += 1
            self._display_bind_page()

    # ================================================================
    # Tab2: 右键菜单
    # ================================================================
    def _show_bind_context_menu(self, pos):
        item = self.bind_tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data["type"]
        trace_code = data["trace_code"]

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #e6e7ea;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 8px 24px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background: #ebecef;
            }
            QMenu::separator {
                height: 1px;
                background: #e6e7ea;
                margin: 4px 12px;
            }
        """)

        copy_action = QAction(f"复制溯源码: {trace_code}", self)
        copy_action.triggered.connect(lambda: self._copy_trace_code(trace_code))
        menu.addAction(copy_action)

        menu.addSeparator()

        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text().strip()

        if item_type in ("standalone", "host") and clipboard_text and clipboard_text != trace_code:
            bind_action = QAction(f"将 {clipboard_text} 绑定到此（作为母版）", self)
            bind_action.triggered.connect(
                lambda: self._do_bind_from_clipboard(trace_code, clipboard_text)
            )
            menu.addAction(bind_action)

        if item_type == "child":
            parent_code = data["parent_code"]
            unbind_action = QAction(f"从 {parent_code} 解绑", self)
            unbind_action.triggered.connect(
                lambda: self._do_unbind(trace_code, parent_code)
            )
            menu.addAction(unbind_action)

        menu.addSeparator()

        refresh_action = QAction("刷新列表", self)
        refresh_action.triggered.connect(self._refresh_bind_list)
        menu.addAction(refresh_action)

        menu.exec(self.bind_tree.viewport().mapToGlobal(pos))

    def _copy_trace_code(self, trace_code: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(trace_code)
        self._show_temp_tip(f"已复制: {trace_code}")

    def _show_temp_tip(self, text: str):
        tip = QLabel(text, self)
        tip.setStyleSheet(
            "background: #333; color: white; padding: 6px 14px; "
            "border-radius: 6px; font-size: 12px;"
        )
        tip.adjustSize()
        global_pos = self.bind_tree.mapToGlobal(
            self.bind_tree.rect().center()
        )
        tip.move(global_pos.x() - tip.width() // 2, global_pos.y() - 30)
        tip.show()

        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, tip.deleteLater)

    def _on_bind_tree_double_click(self, item, column):
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if data:
            self._copy_trace_code(data["trace_code"])

    # ================================================================
    # Tab2: 绑定/解绑操作
    # ================================================================
    def _do_bind_from_clipboard(self, parent_trace: str, child_trace: str):
        reply = QMessageBox.question(
            self, "确认绑定",
            f"将视频 [{child_trace}] 绑定到母版 [{parent_trace}] ?\n\n"
            f"绑定后，{child_trace} 的数据会归入 {parent_trace} 统计。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        user_id = self.current_user.get("user_id") if self.current_user else None
        self.bind_worker = BindWorker(
            parent_trace_code=parent_trace,
            child_trace_codes=[child_trace],
            action="bind",
            user_id=user_id
        )
        self.bind_worker.log.connect(self._bind_log_msg)
        self.bind_worker.finished.connect(self._on_bind_op_finished)
        self.bind_worker.start()

    def _do_unbind(self, child_trace: str, parent_trace: str):
        reply = QMessageBox.question(
            self, "确认解绑",
            f"将视频 [{child_trace}] 从母版 [{parent_trace}] 解绑?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        user_id = self.current_user.get("user_id") if self.current_user else None
        self.bind_worker = BindWorker(
            parent_trace_code=parent_trace,
            child_trace_codes=[child_trace],
            action="unbind",
            user_id=user_id
        )
        self.bind_worker.log.connect(self._bind_log_msg)
        self.bind_worker.finished.connect(self._on_bind_op_finished)
        self.bind_worker.start()

    def _bind_log_msg(self, msg: str):
        print(f"[绑定] {msg}")

    def _on_bind_op_finished(self, success: bool, msg: str):
        if success:
            self._refresh_bind_list()
        QMessageBox.information(self, "操作结果", msg)

    # ================================================================
    # 日志
    # ================================================================
    def _log(self, msg: str):
        self.log_text.appendPlainText(msg)

    def get_params(self) -> dict:
        return {}
