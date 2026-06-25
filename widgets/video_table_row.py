import os
import tempfile
import subprocess
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QCheckBox, QLabel, QLineEdit,
    QMessageBox, QApplication, QToolButton, QMenu, QInputDialog
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from widgets.thumbnail_label import ThumbnailLabel
from utils.ffmpeg_utils import get_video_thumbnail


class VideoTableRow(QWidget):
    """视频表格行"""

    def __init__(self, data, seq_num=0, view_mode="local", parent=None):
        super().__init__(parent)
        self.seq_num = seq_num
        self.view_mode = view_mode
        self.trace_code = ""
        self.record_date = ""
        self.owner_name = ""
        self.operator_name = ""
        self.bind_status = {}  # 绑定状态
        self.info = {}

        try:
            if view_mode == "local":
                self.filename, self.filepath, self.info = data[0], data[1], data[2]
                self.operator_name = data[3] if len(data) > 3 else "未指定"
            else:
                # 作品模式：(trace_code, video_path, record_date, owner_name, filename, info, bind_status)
                self.trace_code, self.filepath, self.record_date, self.owner_name = data[0], data[1], data[2], data[3]
                self.filename = data[4] if len(data) > 4 else Path(self.filepath).name
                self.bind_status = data[6] if len(data) > 6 else {}
                from pathlib import Path
        except:
            self.filepath = ""
            self.filename = "解析异常"

        self.index = 0
        self.is_editing = False
        self.thumbnail_path = None
        self.setup_ui()
        self.setup_events()
        self.generate_thumbnail()

    def setup_ui(self):
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {background-color: transparent; border-bottom:1px solid #e8e8e8;}
            QWidget:hover {background-color:#f5f7fa;}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        # 1. 全局自增序号
        lbl_seq = QLabel(str(self.seq_num))
        lbl_seq.setFixedWidth(30)
        lbl_seq.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_seq)

        # 2. 复选框
        self.check_box = QCheckBox()
        self.check_box.setFixedWidth(30)
        layout.addWidget(self.check_box)

        # 3. 缩略图
        self.thumbnail_label = ThumbnailLabel(self.filepath)
        self.thumbnail_label.clicked.connect(self.open_video)
        self.thumbnail_label.setStyleSheet("""
            ThumbnailLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 3px;
                color: #666;
                font-size: 18px;
                min-width: 50px;
                min-height: 32px;
                max-width: 50px;
                max-height: 32px;
            }
            ThumbnailLabel:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.thumbnail_label)

        if self.view_mode == "local":
            # ========== 本地文件夹列 ==========
            # 文件名
            self.name_label = QLabel(self.filename)
            self.name_label.setFixedWidth(160)
            self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.name_label.setStyleSheet("font-size:12px;background:transparent;")
            self.name_edit = QLineEdit(self.filename)
            self.name_edit.setFixedWidth(160)
            self.name_edit.hide()
            self.name_edit.returnPressed.connect(self.finish_rename)
            self.name_edit.editingFinished.connect(self.finish_rename)
            layout.addWidget(self.name_label)
            layout.addWidget(self.name_edit)

            # 分辨率
            res = f"{self.info.get('width', 'N/A')}x{self.info.get('height', 'N/A')}"
            res_label = QLabel(res)
            res_label.setFixedWidth(100)
            res_label.setAlignment(Qt.AlignCenter)
            res_label.setStyleSheet("font-size:12px;color:#555;background:transparent;")
            layout.addWidget(res_label)

            # 横竖屏
            ori = self.info.get("orientation", "N/A")
            ori_icon = "📱" if ori == "竖屏" else "🖥️" if ori == "横屏" else "❓"
            ori_label = QLabel(f"{ori_icon} {ori}")
            ori_label.setFixedWidth(70)
            ori_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(ori_label)

            # 帧率
            fps_label = QLabel(f"{self.info.get('fps', 'N/A')} fps")
            fps_label.setFixedWidth(65)
            fps_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(fps_label)

            # 码率
            br_label = QLabel(self.info.get("bitrate", "N/A"))
            br_label.setFixedWidth(75)
            br_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(br_label)

            # 时长
            dur_label = QLabel(self.info.get("duration", "N/A"))
            dur_label.setFixedWidth(55)
            dur_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(dur_label)

            # 运营列
            self.operator_label = QLabel(self.operator_name)
            self.operator_label.setFixedWidth(60)
            self.operator_label.setAlignment(Qt.AlignCenter)
            self.operator_label.setStyleSheet("font-size:11px;color:#555;background:transparent;")
            layout.addWidget(self.operator_label)

        else:
            # ========== 我的作品数据库列 ==========
            # 溯源码
            trace_lbl = QLabel(self.trace_code)
            trace_lbl.setFixedWidth(180)
            layout.addWidget(trace_lbl)

            # 归属剪辑姓名
            owner_lbl = QLabel(self.owner_name)
            owner_lbl.setFixedWidth(100)
            layout.addWidget(owner_lbl)

            # 日期
            date_lbl = QLabel(str(self.record_date))
            date_lbl.setFixedWidth(110)
            layout.addWidget(date_lbl)

            # 视频路径
            path_lbl = QLabel(self.filepath)
            path_lbl.setFixedWidth(220)
            layout.addWidget(path_lbl)

        # ========== 操作下拉按钮（只在我的作品模式下显示） ==========
        self.operate_btn = QToolButton()
        self.operate_btn.setText("操作")
        self.operate_btn.setPopupMode(QToolButton.InstantPopup)
        self.operate_btn.setFixedWidth(55)
        self.operate_btn.setVisible(self.view_mode == "work")
        self.operate_btn.setStyleSheet("""
            QToolButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)

        operate_menu = QMenu(self.operate_btn)
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
        self.action_bind = operate_menu.addAction("🔗 绑定")
        self.action_bind.triggered.connect(self.on_bind_action)
        self.action_bound = operate_menu.addAction("✅ 已绑定")
        self.action_bound.triggered.connect(self.on_bound_action)
        self.operate_btn.setMenu(operate_menu)
        layout.addWidget(self.operate_btn)
        # ========== 新增结束 ==========

        # 状态列（两种模式都保留）
        self.status_label = QLabel("⏳")
        self.status_label.setFixedWidth(30)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background:transparent;")

        # 如果是我的作品模式且有绑定状态，显示绑定图标
        if self.view_mode == "work" and self.bind_status:
            self.status_label.setText("🔗")
            self.status_label.setToolTip(f"已绑定到: {self.bind_status.get('bind_trace', '')}")
            self.status_label.setStyleSheet("color: #409eff; background: transparent;")

        layout.addWidget(self.status_label)

        layout.addStretch()

    def setup_events(self):
        if hasattr(self, "name_label"):
            self.name_label.mouseDoubleClickEvent = self.start_rename
        self.check_box.stateChanged.connect(lambda: self.on_check_change())

    def generate_thumbnail(self):
        """生成视频缩略图"""
        try:
            temp_dir = tempfile.gettempdir()
            thumb_path = os.path.join(temp_dir, f"thumb_{abs(hash(self.filepath))}.jpg")

            if os.path.exists(thumb_path):
                self.load_thumbnail(thumb_path)
                return

            if get_video_thumbnail(self.filepath, thumb_path):
                self.thumbnail_path = thumb_path
                self.load_thumbnail(thumb_path)
        except Exception:
            pass

    def load_thumbnail(self, path):
        """加载缩略图"""
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_label.setPixmap(scaled)
                self.thumbnail_label.setText("")
        except:
            pass

    def start_rename(self, event):
        """开始重命名"""
        if not self.is_editing:
            self.is_editing = True
            self.name_label.hide()
            self.name_edit.setText(self.filename)
            self.name_edit.show()
            self.name_edit.setFocus()
            self.name_edit.selectAll()

    def finish_rename(self):
        """完成重命名"""
        if self.is_editing:
            new_name = self.name_edit.text().strip()
            if new_name and new_name != self.filename:
                old_path = self.filepath
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                try:
                    os.rename(old_path, new_path)
                    self.filename = new_name
                    self.filepath = new_path
                    self.name_label.setText(new_name)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"重命名失败: {str(e)}")
            self.name_edit.hide()
            self.name_label.show()
            self.is_editing = False

    def open_video(self):
        import sys
        if not self.filepath or not os.path.exists(self.filepath):
            QMessageBox.information(self, "提示", "视频文件不存在")
            return
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", self.filepath])
            elif sys.platform == "win32":
                os.startfile(self.filepath)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    # ========== 绑定功能 ==========
    def on_bind_action(self):
        """绑定操作 - 将当前视频绑定到另一个视频"""
        if self.view_mode != "work":
            QMessageBox.information(self, "提示", "仅在'我的作品'模式下可绑定")
            return

        # 弹出对话框，输入要绑定的溯源码
        bind_trace, ok = QInputDialog.getText(
            self,
            "绑定视频",
            f"请输入要绑定的视频溯源码\n当前视频: {self.trace_code}\n\n说明: 当前视频将被绑定到输入的溯源码上",
            text=""
        )

        if not ok or not bind_trace:
            return

        bind_trace = bind_trace.strip()
        if bind_trace == self.trace_code:
            QMessageBox.warning(self, "提示", "不能绑定到自身")
            return

        # 调用绑定逻辑
        self._do_bind(bind_trace)

    def _do_bind(self, bind_trace: str):
        """执行绑定"""
        import pymysql
        from config import DB_CFG

        conn = None
        cur = None
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            # 1. 检查被绑定的溯源码是否存在
            cur.execute("SELECT id FROM video_trace WHERE trace_code = %s", (bind_trace,))
            if not cur.fetchone():
                QMessageBox.warning(self, "提示", f"溯源码 {bind_trace} 不存在")
                return

            # 2. 检查当前视频是否已经被绑定
            cur.execute("SELECT id FROM video_bind WHERE trace_code = %s", (self.trace_code,))
            if cur.fetchone():
                QMessageBox.warning(self, "提示", f"视频 {self.trace_code} 已经被绑定，不能重复绑定")
                return

            # 3. 检查目标视频是否已经被绑定（防止串联）
            cur.execute("SELECT id FROM video_bind WHERE trace_code = %s", (bind_trace,))
            if cur.fetchone():
                QMessageBox.warning(self, "提示", f"视频 {bind_trace} 已经被绑定，不能作为绑定目标")
                return

            # 4. 获取当前用户ID
            user_id = None
            if self.parent() and hasattr(self.parent(), 'parent_ref'):
                parent = self.parent()
                if parent.parent_ref and hasattr(parent.parent_ref, 'current_user'):
                    user_id = parent.parent_ref.current_user.get("user_id")

            # 5. 执行绑定
            cur.execute("""
                INSERT INTO video_bind (trace_code, bind_trace_code, user_id, bind_time)
                VALUES (%s, %s, %s, NOW())
            """, (self.trace_code, bind_trace, user_id))

            conn.commit()

            # 更新界面状态
            self.status_label.setText("🔗")
            self.status_label.setToolTip(f"已绑定到: {bind_trace}")
            self.status_label.setStyleSheet("color: #409eff; background: transparent;")

            QMessageBox.information(self, "成功", f"✅ 绑定成功!\n{self.trace_code} -> {bind_trace}")

        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "错误", f"绑定失败: {str(e)}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def on_bound_action(self):
        """已绑定操作 - 查看绑定关系"""
        if self.view_mode != "work":
            QMessageBox.information(self, "提示", "仅在'我的作品'模式下可查看")
            return

        self._show_bind_info()

    def _show_bind_info(self):
        """显示绑定信息"""
        import pymysql
        from config import DB_CFG
        from PySide6.QtWidgets import QMessageBox

        conn = None
        cur = None
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            # 1. 查询当前视频被谁绑定（作为被绑定方）
            cur.execute("""
                SELECT bind_trace_code, user_id, bind_time 
                FROM video_bind 
                WHERE trace_code = %s
            """, (self.trace_code,))
            bound_to = cur.fetchone()

            # 2. 查询当前视频绑定了谁（作为绑定方）
            cur.execute("""
                SELECT trace_code, user_id, bind_time 
                FROM video_bind 
                WHERE bind_trace_code = %s
            """, (self.trace_code,))
            bound_from = cur.fetchall()

            # 构建显示信息
            info = f"📋 绑定关系 - {self.trace_code}\n"
            info += "=" * 40 + "\n\n"

            if bound_to:
                info += f"🔗 被绑定到: {bound_to[0]}\n"
                info += f"  操作人ID: {bound_to[1]}\n"
                info += f"  时间: {bound_to[2]}\n"
            else:
                info += "❌ 未被绑定到任何视频\n"

            info += "\n"

            if bound_from:
                info += f"📌 绑定了以下视频 ({len(bound_from)} 个):\n"
                for bf in bound_from:
                    info += f"  - {bf[0]} (操作人ID: {bf[1]}, 时间: {bf[2]})\n"
            else:
                info += "❌ 没有绑定任何视频\n"

            # 显示对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(f"绑定关系 - {self.trace_code}")
            msg_box.setText(info)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询绑定信息失败: {str(e)}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    # ========== 绑定功能结束 ==========

    def set_processing(self):
        """设置处理中状态"""
        self.status_label.setText("⏳")
        self.status_label.setStyleSheet("color: #f39c12; background: transparent;")

    def set_done(self):
        """设置完成状态"""
        self.status_label.setText("✅")
        self.status_label.setStyleSheet("color: #27ae60; background: transparent;")

    def set_error(self):
        """设置错误状态"""
        self.status_label.setText("❌")
        self.status_label.setStyleSheet("color: #e74c3c; background: transparent;")

    def on_check_change(self):
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, "update_stats"):
            parent_widget.update_stats()