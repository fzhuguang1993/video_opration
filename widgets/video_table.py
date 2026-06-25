# widgets/video_table.py
"""视频表格控件 - QTableWidget 实现 (PySide6)"""
import os
import re
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLabel, QMessageBox, QComboBox, QCheckBox, QWidget as QWidgetBase,
    QToolButton, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont,QAction
from config import PAGE_SIZE, DB_CFG
from utils.ffmpeg_utils import get_video_info
from utils.file_utils import get_video_files, has_trace_code, extract_trace_code
from widgets.thumbnail_label import ThumbnailLabel
import pymysql


class VideoTableWidget(QWidget):
    """视频表格控件 - QTableWidget 实现"""

    file_renamed = Signal(str, str, str)  # PySide6 使用 Signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ref = parent
        self.all_videos = []
        self.current_page = 0
        self.view_mode = "local"
        self.page_size = PAGE_SIZE
        self.checkboxes = {}
        self.is_all_selected = False
        self.context_menu = None

        self.setup_ui()
        self.setup_context_menu()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ===== 工具栏 =====
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        toolbar.setContentsMargins(0, 0, 0, 0)

        # ✅ 全选按钮 - 幽灵按钮
        self.select_all_btn = QPushButton("☑ 全选")
        self.select_all_btn.setObjectName("ghost_btn")
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        self.select_all_btn.setFixedSize(80, 30)
        toolbar.addWidget(self.select_all_btn)

        # ✅ 运营下拉框
        self.operator_combo = QComboBox()
        self.operator_combo.setObjectName("combo_compact")
        self.operator_combo.setFixedSize(130, 30)
        self.operator_combo.addItem("选择运营", None)
        self.operator_combo.setEnabled(False)
        self.operator_combo.setVisible(True)
        toolbar.addWidget(self.operator_combo)

        # ✅ 溯源按钮 - 主按钮
        self.trace_btn = QPushButton("🔍 溯源")
        self.trace_btn.setObjectName("primary_btn")
        self.trace_btn.clicked.connect(self.on_trace_action)
        self.trace_btn.setVisible(False)
        self.trace_btn.setFixedSize(80, 30)
        toolbar.addWidget(self.trace_btn)

        # ===== 返回全部按钮 - 成功按钮 =====
        self.show_all_btn = QPushButton("📋 全部视频")
        self.show_all_btn.setObjectName("success_btn")
        self.show_all_btn.clicked.connect(self.show_all_videos)
        self.show_all_btn.setVisible(False)
        self.show_all_btn.setFixedSize(100, 30)
        toolbar.addWidget(self.show_all_btn)

        # ===== 弹簧 =====
        toolbar.addStretch()

        # ===== 搜索框 =====
        search_label = QLabel("🔍")
        search_label.setFixedSize(20, 30)
        search_label.setObjectName("search_label")
        toolbar.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("搜索文件名...")
        self.search_input.textChanged.connect(self.filter_videos)
        self.search_input.setFixedSize(160, 30)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        # ===== QTableWidget =====
        self.table = QTableWidget()
        self.table.setObjectName("video_table")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        self.table.setDragEnabled(False)
        self.table.setDragDropMode(QAbstractItemView.NoDragDrop)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.set_header_by_view_mode()
        layout.addWidget(self.table)

        # ===== 分页栏 =====
        page_layout = QHBoxLayout()
        page_layout.setSpacing(8)

        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.setObjectName("ghost_btn")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setFixedSize(80, 28)

        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.setObjectName("ghost_btn")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        self.next_btn.setFixedSize(80, 28)

        self.page_label = QLabel("第 0/0 页")
        self.page_label.setObjectName("page_label")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setFixedWidth(100)

        self.info_label = QLabel("共 0 个视频")
        self.info_label.setObjectName("info_label")
        self.info_label.setAlignment(Qt.AlignRight)

        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        page_layout.addWidget(self.info_label)
        layout.addLayout(page_layout)

    def setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = QMenu(self)

        refresh_action = QAction("🔄 刷新", self)
        refresh_action.triggered.connect(self.refresh)
        self.context_menu.addAction(refresh_action)

        self.context_menu.addSeparator()

        select_all_action = QAction("✅ 全选", self)
        select_all_action.triggered.connect(lambda: self.toggle_select_all())
        self.context_menu.addAction(select_all_action)

        invert_action = QAction("🔄 反选", self)
        invert_action.triggered.connect(self.invert_selection)
        self.context_menu.addAction(invert_action)

        deselect_action = QAction("⬜ 取消全选", self)
        deselect_action.triggered.connect(self.deselect_all)
        self.context_menu.addAction(deselect_action)

        self.context_menu.addSeparator()

        clear_action = QAction("🗑️ 清空列表", self)
        clear_action.triggered.connect(self.clear_all)
        self.context_menu.addAction(clear_action)

    def show_context_menu(self, pos):
        """显示右键菜单"""
        self.context_menu.exec_(self.table.viewport().mapToGlobal(pos))

    def set_header_by_view_mode(self):
        """根据视图模式设置表头"""
        self.table.setSortingEnabled(False)

        if self.view_mode == "local":
            headers = ["", "序号", "缩略图", "文件名", "分辨率", "方向", "帧率", "码率", "时长", "状态"]
            widths = [40, 45, 65, 180, 100, 70, 60, 70, 60, 50]
        else:
            headers = ["", "序号", "溯源码", "归属剪辑", "日期", "视频路径", "操作", "状态"]
            widths = [40, 45, 180, 100, 110, 220, 55, 50]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for i, w in enumerate(widths):
            self.table.setColumnWidth(i, w)

        self.table.setSortingEnabled(True)

    def toggle_select_all(self):
        """切换全选/取消全选（反选）"""
        if not self.checkboxes:
            return

        all_checked = all(cb.isChecked() for cb in self.checkboxes.values())
        none_checked = not any(cb.isChecked() for cb in self.checkboxes.values())

        if all_checked:
            self.invert_selection()
            self.select_all_btn.setText("✅ 全选")
            self.is_all_selected = False
        elif none_checked:
            self.select_all()
            self.select_all_btn.setText("⬜ 取消全选")
            self.is_all_selected = True
        else:
            self.select_all()
            self.select_all_btn.setText("⬜ 取消全选")
            self.is_all_selected = True

    def invert_selection(self):
        """反选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(not checkbox.isChecked())
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

    def select_all(self):
        """全选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
        self.select_all_btn.setText("⬜ 取消全选")
        self.is_all_selected = True

    def deselect_all(self):
        """取消全选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

    def load_videos(self, folder_path):
        """加载本地视频"""
        self.view_mode = "local"
        self.set_header_by_view_mode()
        self.all_videos.clear()
        self.current_page = 0
        self.checkboxes.clear()
        self.show_all_btn.setVisible(False)
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

        self.trace_btn.setVisible(True)
        self.search_input.setPlaceholderText("搜索文件名...")

        user_info = None
        if self.parent_ref and hasattr(self.parent_ref, 'current_user'):
            user_info = self.parent_ref.current_user

        user_id = user_info.get("user_id") if user_info else None

        file_list = get_video_files(folder_path)

        trace_owner_map = {}
        if user_id:
            conn = None
            cur = None
            try:
                conn = pymysql.connect(**DB_CFG)
                cur = conn.cursor()
                cur.execute("SELECT trace_code, user_id FROM video_trace")
                results = cur.fetchall()
                for trace_code, owner_id in results:
                    trace_owner_map[trace_code] = owner_id
            except Exception as e:
                print(f"查询溯源码归属失败: {e}")
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

        for f in file_list:
            filename = Path(f).name
            info = get_video_info(f)
            trace_code = extract_trace_code(filename)

            if trace_code:
                owner_id = trace_owner_map.get(trace_code)
                if owner_id == user_id:
                    continue
                elif owner_id is not None:
                    continue
                else:
                    self.all_videos.append((filename, f, info, "未指定", "⚠️ 无归属"))
            else:
                self.all_videos.append((filename, f, info, "未指定", ""))

        self.refresh_display("")

    def load_my_works_list(self, db_rows):
        """加载我的作品"""
        self.view_mode = "work"
        self.set_header_by_view_mode()
        self.all_videos.clear()
        self.current_page = 0
        self.checkboxes.clear()
        self.show_all_btn.setVisible(False)
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

        self.trace_btn.setVisible(False)
        self.search_input.setPlaceholderText("搜索溯源码或文件名...")

        bind_map = self._get_bind_map()

        for row in db_rows:
            trace_code, video_path, record_date, owner_name = row
            filename = Path(video_path).name
            info = get_video_info(video_path)
            bind_status = bind_map.get(trace_code, {})
            self.all_videos.append((trace_code, video_path, record_date, owner_name, filename, info, bind_status))

        self.refresh_display("")

    def refresh_display(self, keyword=""):
        """刷新显示"""
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.checkboxes.clear()
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

        filtered = []
        for item in self.all_videos:
            if self.view_mode == "local":
                filename = item[0]
                if keyword.lower() in filename.lower():
                    filtered.append(item)
            else:
                filename = item[4]
                trace_code = item[0]
                if keyword.lower() in filename.lower() or keyword.lower() in trace_code.lower():
                    filtered.append(item)

        total = len(filtered)
        total_page = max(1, (total + self.page_size - 1) // self.page_size)

        if self.current_page >= total_page:
            self.current_page = total_page - 1
        if self.current_page < 0:
            self.current_page = 0

        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        page_data = filtered[start:end]

        self.table.setRowCount(len(page_data))

        group_seq = 0

        for row, item in enumerate(page_data):
            if self.view_mode == "local":
                filename, filepath, info, operator, status = item
                self._add_local_row(row, row + 1, filename, filepath, info, operator, status)
            else:
                trace_code, video_path, record_date, owner_name, filename, info, bind_status = item[:7]
                is_host = item[7] if len(item) > 7 else False
                is_bind = item[8] if len(item) > 8 else False

                if is_bind:
                    group_seq = 1
                else:
                    group_seq += 1

                self._add_work_row(row, group_seq, trace_code, video_path, record_date, owner_name, filename,
                                   bind_status, is_host, is_bind)

        self.table.setSortingEnabled(True)

        self.page_label.setText(f"第 {self.current_page + 1}/{total_page} 页")
        self.info_label.setText(f"共 {total} 个视频")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_page - 1)

    def _add_local_row(self, row, seq, filename, filepath, info, operator, status):
        """添加本地模式行"""
        checkbox = QCheckBox()
        checkbox_widget = QWidgetBase()
        cb_layout = QHBoxLayout(checkbox_widget)
        cb_layout.addWidget(checkbox)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, checkbox_widget)
        self.checkboxes[row] = checkbox

        item = QTableWidgetItem(str(seq))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, item)

        thumbnail_label = ThumbnailLabel(filepath)
        thumbnail_label.setFixedSize(50, 32)
        thumbnail_label.clicked.connect(lambda: self._open_video(filepath))
        thumbnail_label.setStyleSheet("""
            ThumbnailLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
        """)
        self._load_thumbnail_for_row(thumbnail_label, filepath)
        self.table.setCellWidget(row, 2, thumbnail_label)

        item = QTableWidgetItem(filename)
        item.setToolTip(filename)
        self.table.setItem(row, 3, item)

        res = f"{info.get('width', 'N/A')}x{info.get('height', 'N/A')}"
        item = QTableWidgetItem(res)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, item)

        ori = info.get("orientation", "N/A")
        ori_icon = "📱" if ori == "竖屏" else "🖥️" if ori == "横屏" else "❓"
        item = QTableWidgetItem(f"{ori_icon} {ori}")
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 5, item)

        fps = info.get("fps", "N/A")
        item = QTableWidgetItem(str(fps) if fps != "N/A" else "N/A")
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 6, item)

        bitrate = info.get("bitrate", "N/A")
        item = QTableWidgetItem(str(bitrate))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 7, item)

        duration = info.get("duration", "N/A")
        item = QTableWidgetItem(str(duration))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 8, item)

        if status == "⚠️ 无归属":
            item = QTableWidgetItem("⚠️")
            item.setToolTip("溯源码无归属")
            item.setForeground(QBrush(QColor(255, 150, 0)))
        else:
            item = QTableWidgetItem("⏳")
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 9, item)

    def _add_work_row(self, row, seq, trace_code, video_path, record_date, owner_name, filename, bind_status,
                      is_host=False, is_bind=False):
        """添加我的作品模式行"""

        # ===== 复选框 =====
        checkbox = QCheckBox()
        checkbox_widget = QWidgetBase()
        cb_layout = QHBoxLayout(checkbox_widget)
        cb_layout.addWidget(checkbox)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, checkbox_widget)
        self.checkboxes[row] = checkbox

        # ===== 确定行角色和底色 =====
        if is_host:
            role = "host"
            bg_color = QColor(255, 235, 235)  # 淡粉色 - 宿主
        elif is_bind:
            role = "bind"
            bg_color = QColor(235, 248, 255)  # 浅蓝色 - 绑定
        else:
            role = "normal"
            bg_color = None

        # ===== 序号 =====
        item = QTableWidgetItem(str(seq))
        item.setTextAlignment(Qt.AlignCenter)
        if bg_color:
            item.setBackground(QBrush(bg_color))
        item.setData(Qt.UserRole, role)  # 设置数据角色
        self.table.setItem(row, 1, item)

        # ===== 溯源码 =====
        item = QTableWidgetItem(trace_code)
        item.setToolTip(trace_code)
        if bg_color:
            item.setBackground(QBrush(bg_color))
        item.setData(Qt.UserRole, role)
        self.table.setItem(row, 2, item)

        # ===== 归属剪辑 =====
        item = QTableWidgetItem(owner_name)
        item.setTextAlignment(Qt.AlignCenter)
        if bg_color:
            item.setBackground(QBrush(bg_color))
        item.setData(Qt.UserRole, role)
        self.table.setItem(row, 3, item)

        # ===== 日期 =====
        item = QTableWidgetItem(str(record_date))
        item.setTextAlignment(Qt.AlignCenter)
        if bg_color:
            item.setBackground(QBrush(bg_color))
        item.setData(Qt.UserRole, role)
        self.table.setItem(row, 4, item)

        # ===== 视频路径 =====
        item = QTableWidgetItem(video_path)
        item.setToolTip(video_path)
        if bg_color:
            item.setBackground(QBrush(bg_color))
        item.setData(Qt.UserRole, role)
        self.table.setItem(row, 5, item)

        # ===== 操作按钮 =====
        operate_btn = QToolButton()
        operate_btn.setText("操作")
        operate_btn.setPopupMode(QToolButton.InstantPopup)
        operate_btn.setFixedWidth(55)

        if is_host:
            btn_color = "#ffd0d0"
            btn_hover = "#ffc0c0"
        elif is_bind:
            btn_color = "#c0e0ff"
            btn_hover = "#b0d0f0"
        else:
            btn_color = "#f0f0f0"
            btn_hover = "#e0e0e0"

        operate_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {btn_color};
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 11px;
            }}
            QToolButton:hover {{
                background-color: {btn_hover};
            }}
            QToolButton::menu-indicator {{
                image: none;
            }}
        """)

        operate_menu = QMenu(operate_btn)
        operate_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #e8f0fe;
            }
        """)
        action_bind = operate_menu.addAction("🔗 绑定")
        action_bind.triggered.connect(lambda: self._on_bind_action(trace_code))
        action_bound = operate_menu.addAction("✅ 已绑定")
        action_bound.triggered.connect(self.load_bound_videos)
        operate_btn.setMenu(operate_menu)
        self.table.setCellWidget(row, 6, operate_btn)

        # ===== 状态图标 =====
        if is_host:
            item = QTableWidgetItem("🔗")
            bind_trace = bind_status.get("bind_trace", "") if bind_status else ""
            item.setToolTip(f"被绑定到: {bind_trace}")
            item.setForeground(QBrush(QColor(255, 100, 100)))
            if bg_color:
                item.setBackground(QBrush(bg_color))
        elif is_bind:
            item = QTableWidgetItem("📌")
            item.setToolTip("绑定了其他视频")
            item.setForeground(QBrush(QColor(64, 158, 255)))
            if bg_color:
                item.setBackground(QBrush(bg_color))
        else:
            item = QTableWidgetItem("⏳")
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, role)
        self.table.setItem(row, 7, item)

    def get_selected_videos(self) -> list:
        """获取选中的视频路径"""
        selected = []
        if self.view_mode == "local":
            for row, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    item = self.table.item(row, 3)
                    if item:
                        filename = item.text()
                        for fname, fpath, info, op, status in self.all_videos:
                            if fname == filename:
                                selected.append(fpath)
                                break
        return selected

    def filter_videos(self, text: str):
        """筛选视频"""
        self.current_page = 0
        self.refresh_display(text)

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_display(self.search_input.text())

    def next_page(self):
        """下一页"""
        filtered = []
        keyword = self.search_input.text()
        for item in self.all_videos:
            if self.view_mode == "local":
                if keyword.lower() in item[0].lower():
                    filtered.append(item)
            else:
                if keyword.lower() in item[4].lower():
                    filtered.append(item)
        total_page = max(1, (len(filtered) + self.page_size - 1) // self.page_size)
        if self.current_page < total_page - 1:
            self.current_page += 1
            self.refresh_display(self.search_input.text())

    def refresh(self):
        """刷新表格"""
        if self.parent_ref and hasattr(self.parent_ref, 'folder_input'):
            folder = self.parent_ref.folder_input.text()
            if folder and os.path.exists(folder):
                self.load_videos(folder)
        self.select_all_btn.setText("✅ 全选")
        self.is_all_selected = False

    def clear_all(self):
        """清空所有视频"""
        if not self.all_videos:
            return
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有视频吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.all_videos.clear()
            self.current_page = 0
            self.refresh_display("")

    def load_bound_videos(self):
        """加载已绑定的视频（占位方法）"""
        QMessageBox.information(self, "提示", "加载已绑定视频功能开发中")

    def show_all_videos(self):
        """显示全部视频"""
        if self.parent_ref and hasattr(self.parent_ref, 'load_my_work_videos'):
            self.parent_ref.load_my_work_videos()
            self.show_all_btn.setVisible(False)

    def _get_bind_map(self) -> dict:
        """获取绑定关系"""
        return {}

    def _on_bind_action(self, trace_code):
        """绑定操作"""
        bind_trace, ok = QInputDialog.getText(
            self,
            "绑定视频",
            f"请输入要绑定的视频溯源码\n当前视频: {trace_code}",
            text=""
        )
        if ok and bind_trace:
            QMessageBox.information(self, "提示", f"绑定功能开发中: {trace_code} -> {bind_trace}")

    def _load_thumbnail_for_row(self, thumbnail_label, filepath):
        """加载缩略图"""
        try:
            import tempfile
            from utils.ffmpeg_utils import get_video_thumbnail
            from PySide6.QtGui import QPixmap

            temp_dir = tempfile.gettempdir()
            thumb_path = os.path.join(temp_dir, f"thumb_{abs(hash(filepath))}.jpg")

            if os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(50, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumbnail_label.setPixmap(scaled)
                    thumbnail_label.setText("")
                    return

            if get_video_thumbnail(filepath, thumb_path):
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(50, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumbnail_label.setPixmap(scaled)
                    thumbnail_label.setText("")
        except Exception as e:
            print(f"加载缩略图失败: {e}")

    def _open_video(self, filepath):
        """打开视频"""
        import sys
        import subprocess
        if not filepath or not os.path.exists(filepath):
            QMessageBox.information(self, "提示", "视频文件不存在")
            return
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", filepath])
            elif sys.platform == "win32":
                os.startfile(filepath)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    # ===== 溯源功能 =====
    def on_trace_action(self):
        """溯源按钮点击事件"""
        selected = self.get_selected_videos()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要溯源的视频")
            return

        user_info = None
        if self.parent_ref and hasattr(self.parent_ref, 'current_user'):
            user_info = self.parent_ref.current_user

        if not user_info:
            QMessageBox.warning(self, "提示", "未获取到用户登录信息")
            return

        role = user_info.get("role")
        real_name = user_info.get("real_name", "")

        operator_name = None
        operator_id = None

        if role == 3:
            current_text = self.operator_combo.currentText()
            if not current_text or current_text == "选择运营":
                QMessageBox.warning(self, "提示", "请先选择运营人员！")
                return
            operator_name = current_text
            operator_data = self.operator_combo.currentData()
            if operator_data:
                operator_id = operator_data.get("id")
        elif role == 2:
            operator_name = real_name
            operator_id = user_info.get("user_id")
        elif role == 1:
            current_text = self.operator_combo.currentText()
            if current_text and current_text != "选择运营":
                operator_name = current_text
                operator_data = self.operator_combo.currentData()
                if operator_data:
                    operator_id = operator_data.get("id")
            else:
                operator_name = real_name
                operator_id = user_info.get("user_id")

        if not operator_name:
            QMessageBox.warning(self, "提示", "请选择有效的运营人员！")
            return

        # 检查溯源码池
        conn = None
        cur = None
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM trace_code_pool WHERE is_used = 0")
            available = cur.fetchone()[0]
            if available < len(selected):
                QMessageBox.warning(
                    self, "提示",
                    f"溯源码池可用数量不足！\n需要: {len(selected)} 个\n可用: {available} 个"
                )
                return
        except Exception as e:
            QMessageBox.warning(self, "提示", f"检查溯源码池失败: {e}")
            return
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        reply = QMessageBox.question(
            self, "确认溯源",
            f"将对 {len(selected)} 个视频进行溯源处理\n\n"
            "操作流程:\n"
            "1. 📦 从溯源码池获取溯源码\n"
            "2. 📝 重命名: 溯源码_日期_剪辑首拼_运营首拼.MP4\n"
            "3. 💾 保存溯源记录到数据库\n"
            "4. 📤 上传到SMB共享文件夹\n\n"
            f"👤 剪辑: {real_name}\n"
            f"👤 运营: {operator_name}\n"
            f"📦 当前可用溯源码: {available} 个\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        user_info_with_operator = user_info.copy()
        user_info_with_operator["operator_name"] = operator_name
        user_info_with_operator["operator_id"] = operator_id

        from widgets.trace_dialog import TraceDialog
        dialog = TraceDialog(selected, user_info_with_operator, self)
        dialog.exec()

        if self.parent_ref and hasattr(self.parent_ref, 'folder_input'):
            folder = self.parent_ref.folder_input.text().strip()
            if folder and os.path.exists(folder):
                self.load_videos(folder)