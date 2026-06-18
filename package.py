import os
import sys
import subprocess
import tempfile
import shutil
import json
import re
from pathlib import Path
from datetime import datetime

# PyQt5 界面
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --- 配置 ---
VERSION = "1.0.0"
PAGE_SIZE = 20


# ------------


def get_ffmpeg_path():
    """获取 FFmpeg 路径（优先使用同目录下的 ffmpeg.exe）"""
    # 检查同目录下是否有 ffmpeg.exe
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 检查同目录
    if os.path.exists(os.path.join(base_dir, 'ffmpeg.exe')):
        return os.path.join(base_dir, 'ffmpeg.exe')
    # 检查同目录下的 bin 文件夹
    if os.path.exists(os.path.join(base_dir, 'bin', 'ffmpeg.exe')):
        return os.path.join(base_dir, 'bin', 'ffmpeg.exe')
    # 检查 ffmpeg 文件夹
    if os.path.exists(os.path.join(base_dir, 'ffmpeg', 'bin', 'ffmpeg.exe')):
        return os.path.join(base_dir, 'ffmpeg', 'bin', 'ffmpeg.exe')

    # 最后用系统 PATH 中的 ffmpeg
    return 'ffmpeg'


def get_ffprobe_path():
    """获取 ffprobe 路径"""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    if os.path.exists(os.path.join(base_dir, 'ffprobe.exe')):
        return os.path.join(base_dir, 'ffprobe.exe')
    if os.path.exists(os.path.join(base_dir, 'bin', 'ffprobe.exe')):
        return os.path.join(base_dir, 'bin', 'ffprobe.exe')
    if os.path.exists(os.path.join(base_dir, 'ffmpeg', 'bin', 'ffprobe.exe')):
        return os.path.join(base_dir, 'ffmpeg', 'bin', 'ffprobe.exe')
    return 'ffprobe'


def get_video_info(file_path):
    """使用 ffprobe 获取视频信息"""
    try:
        ffprobe = get_ffprobe_path()
        cmd = [
            ffprobe, '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        info = {
            'width': 'N/A',
            'height': 'N/A',
            'fps': 'N/A',
            'codec': 'N/A',
            'bitrate': 'N/A',
            'duration': 'N/A',
            'orientation': 'N/A',
            'audio_bitrate': 'N/A',
        }

        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                info['width'] = stream.get('width', 'N/A')
                info['height'] = stream.get('height', 'N/A')
                info['codec'] = stream.get('codec_name', 'N/A')

                fps = stream.get('r_frame_rate', '0/0')
                if '/' in str(fps):
                    try:
                        num, den = fps.split('/')
                        info['fps'] = f"{int(num) / int(den):.2f}" if int(den) > 0 else 'N/A'
                    except:
                        info['fps'] = 'N/A'

                if info['width'] != 'N/A' and info['height'] != 'N/A':
                    info['orientation'] = '竖屏' if info['width'] < info['height'] else '横屏'

        fmt = data.get('format', {})
        bitrate = fmt.get('bit_rate', '0')
        if bitrate != '0' and bitrate != 'N/A':
            info['bitrate'] = f"{int(bitrate) / 1000:.0f} kbps"

        duration = fmt.get('duration', '0')
        if duration != '0' and duration != 'N/A':
            try:
                sec = float(duration)
                minutes = int(sec // 60)
                seconds = int(sec % 60)
                info['duration'] = f"{minutes}:{seconds:02d}"
            except:
                info['duration'] = 'N/A'

        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                abr = stream.get('bit_rate', '0')
                if abr != '0' and abr != 'N/A':
                    info['audio_bitrate'] = f"{int(abr) / 1000:.0f} kbps"
                    break

        return info
    except Exception as e:
        return None


def get_video_thumbnail(file_path, output_path, time_pos=1.0):
    """从视频中提取缩略图"""
    try:
        ffmpeg = get_ffmpeg_path()
        cmd = [
            ffmpeg, '-i', file_path,
            '-ss', str(time_pos),
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            '-y', output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


class ClickableLabel(QLabel):
    """可点击的标签，双击弹出输入框"""
    value_changed = pyqtSignal(int)

    def __init__(self, text="", min_val=0, max_val=9999, is_float=False, parent=None):
        super().__init__(text, parent)
        self.min_val = min_val
        self.max_val = max_val
        self.is_float = is_float
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #f5f6fa;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QLabel:hover {
                background-color: #e8eaf0;
                border-color: #3498db;
            }
        """)
        self.setToolTip("双击输入数值")

    def mouseDoubleClickEvent(self, event):
        if self.is_float:
            current_val = float(self.text())
            value, ok = QInputDialog.getDouble(
                self, "输入数值",
                f"请输入数值 ({self.min_val}-{self.max_val}):",
                current_val, self.min_val, self.max_val, 2
            )
            if ok:
                int_val = int(round(value))
                self.setText(f"{int_val / 100:.2f}")
                self.value_changed.emit(int_val)
        else:
            current_val = int(self.text())
            value, ok = QInputDialog.getInt(
                self, "输入数值",
                f"请输入数值 ({self.min_val}-{self.max_val}):",
                current_val, self.min_val, self.max_val
            )
            if ok:
                self.setText(str(value))
                self.value_changed.emit(value)


class ThumbnailLabel(QLabel):
    """缩略图控件 - 悬停预览"""

    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setFixedSize(50, 32)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; font-size: 20px;")
        self.setText("🎬")
        self.preview_window = None
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_preview)

    def enterEvent(self, event):
        self.hover_timer.start(300)

    def leaveEvent(self, event):
        self.hover_timer.stop()
        self.close_preview()

    def show_preview(self):
        """弹出预览窗口"""
        if self.preview_window and self.preview_window.isVisible():
            return

        self.preview_window = QWidget()
        self.preview_window.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.preview_window.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)

        layout = QVBoxLayout(self.preview_window)
        layout.setContentsMargins(8, 8, 8, 8)

        # 显示预览信息
        info_label = QLabel(f"🎬\n{os.path.basename(self.filepath)}")
        info_label.setStyleSheet("color: white; font-size: 14px;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        self.preview_window.resize(280, 160)

        # 显示在鼠标位置
        pos = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()
        x = min(pos.x() + 10, screen.width() - self.preview_window.width() - 10)
        y = min(pos.y() + 10, screen.height() - self.preview_window.height() - 10)
        self.preview_window.move(x, y)
        self.preview_window.show()

        # 点击窗口关闭
        self.preview_window.mousePressEvent = lambda e: self.close_preview()

    def close_preview(self):
        if self.preview_window:
            self.preview_window.close()
            self.preview_window = None


class VideoTableRow(QWidget):
    """视频表格行"""

    def __init__(self, filename, filepath, info, index, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.filepath = filepath
        self.info = info or {}
        self.index = index
        self.parent_ref = parent
        self.is_editing = False
        self.thumbnail_path = None
        self.setup_ui()
        self.setup_events()
        self.generate_thumbnail()

    def setup_ui(self):
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom: 1px solid #e8e8e8;
            }
            QWidget:hover {
                background-color: #f5f7fa;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        # 复选框
        self.check_box = QCheckBox()
        self.check_box.setFixedWidth(30)
        layout.addWidget(self.check_box)

        # 缩略图
        self.thumbnail_label = ThumbnailLabel(self.filepath)
        layout.addWidget(self.thumbnail_label)

        # 文件名（可双击编辑）
        self.name_label = QLabel(self.filename)
        self.name_label.setFixedWidth(160)
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.name_label.setStyleSheet("font-size: 12px; background: transparent;")
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
        res_label.setStyleSheet("font-size: 12px; color: #555; background: transparent;")
        layout.addWidget(res_label)

        # 方向
        orientation = self.info.get('orientation', 'N/A')
        ori_icon = "📱" if orientation == "竖屏" else "🖥️" if orientation == "横屏" else "❓"
        ori_label = QLabel(f"{ori_icon} {orientation}")
        ori_label.setFixedWidth(70)
        ori_label.setAlignment(Qt.AlignCenter)
        ori_label.setStyleSheet("font-size: 12px; color: #555; background: transparent;")
        layout.addWidget(ori_label)

        # 帧率
        fps_label = QLabel(f"{self.info.get('fps', 'N/A')} fps")
        fps_label.setFixedWidth(65)
        fps_label.setAlignment(Qt.AlignCenter)
        fps_label.setStyleSheet("font-size: 12px; color: #555; background: transparent;")
        layout.addWidget(fps_label)

        # 码率
        br_label = QLabel(self.info.get('bitrate', 'N/A'))
        br_label.setFixedWidth(75)
        br_label.setAlignment(Qt.AlignCenter)
        br_label.setStyleSheet("font-size: 12px; color: #555; background: transparent;")
        layout.addWidget(br_label)

        # 时长
        dur_label = QLabel(self.info.get('duration', 'N/A'))
        dur_label.setFixedWidth(55)
        dur_label.setAlignment(Qt.AlignCenter)
        dur_label.setStyleSheet("font-size: 12px; color: #555; background: transparent;")
        layout.addWidget(dur_label)

        # 状态
        self.status_label = QLabel("⏳")
        self.status_label.setFixedWidth(30)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def setup_events(self):
        self.name_label.mouseDoubleClickEvent = self.start_rename
        self.mouseDoubleClickEvent = self.open_video

    def generate_thumbnail(self):
        try:
            temp_dir = tempfile.gettempdir()
            thumb_path = os.path.join(temp_dir, f"thumb_{abs(hash(self.filepath))}.jpg")

            if os.path.exists(thumb_path):
                self.load_thumbnail(thumb_path)
                return

            if get_video_thumbnail(self.filepath, thumb_path):
                self.thumbnail_path = thumb_path
                self.load_thumbnail(thumb_path)
        except Exception as e:
            pass

    def load_thumbnail(self, path):
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_label.setPixmap(scaled)
                self.thumbnail_label.setText("")
        except:
            pass

    def start_rename(self, event):
        if not self.is_editing:
            self.is_editing = True
            self.name_label.hide()
            self.name_edit.setText(self.filename)
            self.name_edit.show()
            self.name_edit.setFocus()
            self.name_edit.selectAll()

    def finish_rename(self):
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

    def open_video(self, event):
        if sys.platform == 'darwin':
            subprocess.run(['open', self.filepath])
        elif sys.platform == 'win32':
            os.startfile(self.filepath)
        else:
            subprocess.run(['xdg-open', self.filepath])

    def set_processing(self):
        self.status_label.setText("⏳")
        self.status_label.setStyleSheet("color: #f39c12; background: transparent;")

    def set_done(self):
        self.status_label.setText("✅")
        self.status_label.setStyleSheet("color: #27ae60; background: transparent;")

    def set_error(self):
        self.status_label.setText("❌")
        self.status_label.setStyleSheet("color: #e74c3c; background: transparent;")


class VideoTableWidget(QWidget):
    """视频表格控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_videos = []
        self.current_page = 0
        self.page_size = PAGE_SIZE
        self.parent_ref = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        self.select_all_btn = QPushButton("✅ 全选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("⬜ 取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)

        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.deselect_all_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()

        toolbar.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件名...")
        self.search_input.textChanged.connect(self.filter_videos)
        self.search_input.setFixedWidth(150)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background: white;
            }
        """)

        self.table_container = QWidget()
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table_layout.setSpacing(0)

        # 表头
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                border-bottom: 2px solid #d0d0d0;
            }
        """)
        header_widget.setFixedHeight(32)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(8)

        headers = [
            ("", 30),
            ("🎬 缩略图", 50),
            ("📹 文件名", 160),
            ("📐 分辨率", 100),
            ("📱 方向", 70),
            ("🎞️ 帧率", 65),
            ("📊 码率", 75),
            ("⏱️ 时长", 55),
            ("状态", 30)
        ]
        for text, width in headers:
            label = QLabel(text)
            label.setFixedWidth(width)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; color: #444; font-size: 11px; background: transparent;")
            header_layout.addWidget(label)
        header_layout.addStretch()

        self.table_layout.addWidget(header_widget)

        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()

        self.table_layout.addWidget(self.rows_widget)
        scroll_area.setWidget(self.table_container)
        layout.addWidget(scroll_area)

        page_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        self.page_label = QLabel("第 0/0 页")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.info_label = QLabel("共 0 个视频")
        self.info_label.setAlignment(Qt.AlignRight)

        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        page_layout.addWidget(self.info_label)
        layout.addLayout(page_layout)

    def load_videos(self, folder_path):
        if not os.path.exists(folder_path):
            return

        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
        self.all_videos = []

        for f in sorted(os.listdir(folder_path)):
            f_path = os.path.join(folder_path, f)
            if os.path.isdir(f_path):
                continue
            ext = Path(f).suffix.lower()
            if ext in video_exts:
                info = get_video_info(f_path)
                self.all_videos.append((f, f_path, info))

        self.current_page = 0
        self.search_input.clear()
        self.refresh_display()

    def add_videos(self, file_paths):
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
        added = 0
        for f_path in file_paths:
            if os.path.isfile(f_path):
                ext = Path(f_path).suffix.lower()
                if ext in video_exts:
                    exists = False
                    for _, existing_path, _ in self.all_videos:
                        if existing_path == f_path:
                            exists = True
                            break
                    if not exists:
                        info = get_video_info(f_path)
                        self.all_videos.append((Path(f_path).name, f_path, info))
                        added += 1

        if added > 0:
            self.current_page = 0
            self.refresh_display()

    def filter_videos(self, text):
        self.current_page = 0
        self.refresh_display(search_text=text)

    def get_filtered_videos(self, search_text=""):
        if not search_text:
            return self.all_videos
        search_lower = search_text.lower()
        return [(f, p, i) for f, p, i in self.all_videos if search_lower in f.lower()]

    def get_selected_videos(self):
        selected = []
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'check_box'):
                if item.widget().check_box.isChecked():
                    selected.append(item.widget().filepath)
        return selected

    def get_video_count(self):
        return len(self.all_videos)

    def refresh_display(self, search_text=""):
        for i in reversed(range(self.rows_layout.count())):
            item = self.rows_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        filtered = self.get_filtered_videos(search_text)
        total = len(filtered)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size) if total > 0 else 1

        if self.current_page >= total_pages:
            self.current_page = total_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)

        for i in range(start, end):
            filename, filepath, info = filtered[i]
            row_widget = VideoTableRow(filename, filepath, info, i, self)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row_widget)

        self.page_label.setText(f"第 {self.current_page + 1}/{total_pages} 页")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)
        self.info_label.setText(f"共 {total} 个视频 | 显示 {start + 1}-{end}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_display(self.search_input.text())

    def next_page(self):
        filtered = self.get_filtered_videos(self.search_input.text())
        total_pages = (len(filtered) + self.page_size - 1) // self.page_size if filtered else 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_display(self.search_input.text())

    def select_all(self):
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'check_box'):
                item.widget().check_box.setChecked(True)

    def deselect_all(self):
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'check_box'):
                item.widget().check_box.setChecked(False)

    def refresh(self):
        folder = self.parent_ref.folder_input.text() if self.parent_ref else ""
        if folder:
            self.load_videos(folder)

    def clear_all(self):
        self.all_videos = []
        self.current_page = 0
        self.refresh_display()


class ParamHintButton(QPushButton):
    """带提示的问号按钮"""

    def __init__(self, hint_text, parent=None):
        super().__init__("?", parent)
        self.hint_text = hint_text
        self.setFixedSize(18, 18)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 9px;
                font-weight: bold;
                font-size: 11px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.setToolTip(hint_text)
        self.clicked.connect(self.show_hint)

    def show_hint(self):
        QMessageBox.information(self, "参数说明", self.hint_text)


class WatermarkWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)
    video_status = pyqtSignal(str, str)

    def __init__(self, input_folder, watermark_path, params, video_list=None, count_mode='all', count=1):
        super().__init__()
        self.input_folder = input_folder
        self.watermark_path = watermark_path
        self.params = params
        self.video_list = video_list or []
        self.count_mode = count_mode
        self.count = count
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            if self.video_list:
                videos_to_process = self.video_list
            else:
                all_videos = []
                video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
                for f in os.listdir(self.input_folder):
                    f_path = os.path.join(self.input_folder, f)
                    if os.path.isdir(f_path):
                        continue
                    ext = Path(f).suffix.lower()
                    if ext in video_exts:
                        all_videos.append(f)
                all_videos = sorted(all_videos)

                if self.count_mode == 'count':
                    videos_to_process = all_videos[:self.count]
                else:
                    videos_to_process = all_videos

            if not videos_to_process:
                self.finished.emit(False, "没有可处理的视频！")
                return

            self.log.emit(f"📹 共 {len(videos_to_process)} 个视频待处理")

            right_margin = self.params['right_margin']
            bottom_y = self.params['bottom_y']
            bounce_speed_x = self.params['bounce_speed_x']
            bounce_speed_y = self.params['bounce_speed_y']
            top_margin = self.params['top_margin']
            bottom_margin = self.params['bottom_margin']
            position_mode = self.params['position_mode']

            total = len(videos_to_process)
            success_count = 0

            for i, video_name in enumerate(videos_to_process):
                if not self._is_running:
                    break

                if os.path.isabs(video_name):
                    input_path = video_name
                    video_name = Path(video_name).name
                else:
                    input_path = os.path.join(self.input_folder, video_name)

                if not os.path.exists(input_path):
                    self.log.emit(f"  ⚠️ 文件不存在: {video_name}")
                    self.video_status.emit(video_name, 'error')
                    continue

                self.video_status.emit(video_name, 'processing')
                base_name = Path(video_name).stem
                today = datetime.now().strftime("%Y-%m-%d")

                mode_names = {1: '右下角', 2: '碰撞反弹', 3: '右下角+碰撞反弹'}
                mode_name = mode_names.get(position_mode, '水印')
                output_name = f"{today}_{base_name}_水印_{mode_name}.mp4"
                output_path = os.path.join(self.input_folder, output_name)

                self.progress.emit(i, f"处理中: {video_name}")
                self.log.emit(f"\n[{i + 1}/{total}] {video_name}")

                cmd = self.build_ffmpeg_command(
                    input_path, output_path,
                    right_margin, bottom_y,
                    bounce_speed_x, bounce_speed_y,
                    top_margin, bottom_margin,
                    position_mode
                )

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    success_count += 1
                    self.video_status.emit(video_name, 'done')
                    self.log.emit(f"  ✅ 成功: {output_name}")
                else:
                    self.video_status.emit(video_name, 'error')
                    self.log.emit(f"  ❌ 失败: {result.stderr[:200]}")

            self.progress.emit(total, "完成")
            msg = f"处理完成！成功: {success_count}/{total}"
            self.finished.emit(True, msg)

        except Exception as e:
            self.finished.emit(False, f"错误: {str(e)}")

    def build_ffmpeg_command(self, input_path, output_path,
                             right_margin, bottom_y,
                             speed_x, speed_y,
                             top_margin, bottom_margin,
                             mode):
        ffmpeg_path = get_ffmpeg_path()

        if mode == 1:
            cmd = [
                ffmpeg_path, '-i', input_path,
                '-i', self.watermark_path,
                '-filter_complex',
                f'[1:v]scale=200:-1,format=rgba[wm];'
                f'[0:v]scale=1080:1920:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,format=rgb24[bg];'
                f'[bg][wm]overlay=W-200-{right_margin}:{bottom_y}:alpha=1',
                '-c:v', 'libx264', '-b:v', '4M', '-r', '30',
                '-c:a', 'aac', '-b:a', '44k',
                '-y', output_path
            ]
        elif mode == 2:
            scroll_range_y = f"(H-200-{top_margin}-{bottom_margin})"
            scroll_range_x = f"(W-200)"
            cmd = [
                ffmpeg_path, '-i', input_path,
                '-i', self.watermark_path,
                '-filter_complex',
                f'[1:v]scale=200:-1,format=rgba[wm];'
                f'[0:v]scale=1080:1920:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,format=rgb24[bg];'
                f'[bg][wm]overlay=x={scroll_range_x}*abs(sin(t*{speed_x})):y={top_margin}+{scroll_range_y}*abs(cos(t*{speed_y})):alpha=1',
                '-c:v', 'libx264', '-b:v', '4M', '-r', '30',
                '-c:a', 'aac', '-b:a', '44k',
                '-y', output_path
            ]
        else:
            scroll_range_y = f"(H-200-{top_margin}-{bottom_margin})"
            scroll_range_x = f"(W-200)"
            cmd = [
                ffmpeg_path, '-i', input_path,
                '-i', self.watermark_path,
                '-filter_complex',
                f'[1:v]scale=200:-1,format=rgba[wm1];'
                f'[1:v]scale=200:-1,format=rgba[wm2];'
                f'[0:v]scale=1080:1920:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,format=rgb24[bg];'
                f'[bg][wm1]overlay=W-200-{right_margin}:{bottom_y}:alpha=1[bg1];'
                f'[bg1][wm2]overlay=x={scroll_range_x}*abs(sin(t*{speed_x})):y={top_margin}+{scroll_range_y}*abs(cos(t*{speed_y})):alpha=1',
                '-c:v', 'libx264', '-b:v', '4M', '-r', '30',
                '-c:a', 'aac', '-b:a', '44k',
                '-y', output_path
            ]
        return cmd


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"🎬 视频水印工具 v{VERSION}")
        self.setMinimumSize(1050, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(12)

        # ========== 左侧面板 ==========
        left_panel = QWidget()
        left_panel.setFixedWidth(420)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        title = QLabel("🎬 视频水印工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 8px; color: #2c3e50;")
        left_layout.addWidget(title)

        # 输入文件夹
        group1 = QGroupBox("📂 视频文件夹")
        group1_layout = QVBoxLayout()
        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("选择视频文件夹...")
        folder_btn = QPushButton("📁 浏览")
        folder_btn.clicked.connect(self.select_folder)
        folder_btn.setFixedWidth(70)
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(folder_btn)
        group1_layout.addLayout(folder_row)
        group1.setLayout(group1_layout)
        left_layout.addWidget(group1)

        # 水印图片
        group2 = QGroupBox("🖼️  水印图片")
        group2_layout = QVBoxLayout()
        watermark_row = QHBoxLayout()
        self.watermark_input = QLineEdit()
        self.watermark_input.setReadOnly(True)
        self.watermark_input.setPlaceholderText("选择水印图片...")
        wm_btn = QPushButton("📁 浏览")
        wm_btn.clicked.connect(self.select_watermark)
        wm_btn.setFixedWidth(70)
        watermark_row.addWidget(self.watermark_input)
        watermark_row.addWidget(wm_btn)
        group2_layout.addLayout(watermark_row)
        group2.setLayout(group2_layout)
        left_layout.addWidget(group2)

        # 处理模式
        group3 = QGroupBox("⚙️  处理模式")
        group3_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["处理选中的视频", "处理前 N 个视频", "处理全部视频"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        group3_layout.addWidget(QLabel("模式:"))
        group3_layout.addWidget(self.mode_combo)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 999)
        self.count_spin.setValue(1)
        self.count_spin.setEnabled(False)
        group3_layout.addWidget(QLabel("N ="))
        group3_layout.addWidget(self.count_spin)
        group3_layout.addStretch()
        group3.setLayout(group3_layout)
        left_layout.addWidget(group3)

        # 水印模式
        group4 = QGroupBox("📍 水印模式")
        group4_layout = QVBoxLayout()
        self.wm_mode_combo = QComboBox()
        self.wm_mode_combo.addItems([
            "右下角 (固定)",
            "碰撞反弹 (全屏移动)",
            "右下角 + 碰撞反弹 (同时)"
        ])
        group4_layout.addWidget(self.wm_mode_combo)
        group4.setLayout(group4_layout)
        left_layout.addWidget(group4)

        # 参数调节
        group5 = QGroupBox("⚙️  参数调节")
        group5_layout = QVBoxLayout()
        group5_layout.setSpacing(4)

        param_header = QHBoxLayout()
        param_header.addWidget(QLabel("参数调节"))
        param_header.addStretch()
        hint_btn = ParamHintButton(
            "参数说明：\n\n"
            "• 右侧边距：水印距离视频右边界的像素\n"
            "• 垂直位置：水印距离视频顶部的像素\n"
            "• 水平速度：碰撞反弹时左右移动的速度\n"
            "• 垂直速度：碰撞反弹时上下移动的速度\n"
            "• 顶部预留：水印不会进入的顶部区域\n"
            "• 底部预留：水印不会进入的底部区域\n\n"
            "💡 双击数值可手动输入"
        )
        param_header.addWidget(hint_btn)
        group5_layout.addLayout(param_header)

        grid = QGridLayout()
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(6)

        # 右侧边距
        grid.addWidget(QLabel("右侧边距:"), 0, 0)
        self.margin_slider = QSlider(Qt.Horizontal)
        self.margin_slider.setRange(0, 500)
        self.margin_slider.setValue(148)
        self.margin_slider.valueChanged.connect(lambda v: self.margin_label.setText(str(v)))
        grid.addWidget(self.margin_slider, 0, 1)
        self.margin_label = ClickableLabel("148", 0, 500)
        self.margin_label.value_changed.connect(self.margin_slider.setValue)
        grid.addWidget(self.margin_label, 0, 2)

        # 垂直位置
        grid.addWidget(QLabel("垂直位置:"), 1, 0)
        self.y_slider = QSlider(Qt.Horizontal)
        self.y_slider.setRange(1000, 1900)
        self.y_slider.setValue(1602)
        self.y_slider.valueChanged.connect(lambda v: self.y_label.setText(str(v)))
        grid.addWidget(self.y_slider, 1, 1)
        self.y_label = ClickableLabel("1602", 1000, 1900)
        self.y_label.value_changed.connect(self.y_slider.setValue)
        grid.addWidget(self.y_label, 1, 2)

        # 水平速度
        grid.addWidget(QLabel("水平速度:"), 2, 0)
        self.speed_x_slider = QSlider(Qt.Horizontal)
        self.speed_x_slider.setRange(0, 100)
        self.speed_x_slider.setValue(30)
        self.speed_x_slider.valueChanged.connect(lambda v: self.speed_x_label.setText(f"{v / 100:.2f}"))
        grid.addWidget(self.speed_x_slider, 2, 1)
        self.speed_x_label = ClickableLabel("0.30", 0, 100, is_float=True)
        self.speed_x_label.value_changed.connect(lambda v: self.speed_x_slider.setValue(v))
        grid.addWidget(self.speed_x_label, 2, 2)

        # 垂直速度
        grid.addWidget(QLabel("垂直速度:"), 3, 0)
        self.speed_y_slider = QSlider(Qt.Horizontal)
        self.speed_y_slider.setRange(0, 100)
        self.speed_y_slider.setValue(40)
        self.speed_y_slider.valueChanged.connect(lambda v: self.speed_y_label.setText(f"{v / 100:.2f}"))
        grid.addWidget(self.speed_y_slider, 3, 1)
        self.speed_y_label = ClickableLabel("0.40", 0, 100, is_float=True)
        self.speed_y_label.value_changed.connect(lambda v: self.speed_y_slider.setValue(v))
        grid.addWidget(self.speed_y_label, 3, 2)

        # 顶部预留
        grid.addWidget(QLabel("顶部预留:"), 4, 0)
        self.top_slider = QSlider(Qt.Horizontal)
        self.top_slider.setRange(0, 500)
        self.top_slider.setValue(250)
        self.top_slider.valueChanged.connect(lambda v: self.top_label.setText(str(v)))
        grid.addWidget(self.top_slider, 4, 1)
        self.top_label = ClickableLabel("250", 0, 500)
        self.top_label.value_changed.connect(self.top_slider.setValue)
        grid.addWidget(self.top_label, 4, 2)

        # 底部预留
        grid.addWidget(QLabel("底部预留:"), 5, 0)
        self.bottom_slider = QSlider(Qt.Horizontal)
        self.bottom_slider.setRange(0, 500)
        self.bottom_slider.setValue(250)
        self.bottom_slider.valueChanged.connect(lambda v: self.bottom_label.setText(str(v)))
        grid.addWidget(self.bottom_slider, 5, 1)
        self.bottom_label = ClickableLabel("250", 0, 500)
        self.bottom_label.value_changed.connect(self.bottom_slider.setValue)
        grid.addWidget(self.bottom_label, 5, 2)

        group5_layout.addLayout(grid)
        group5.setLayout(group5_layout)
        left_layout.addWidget(group5)

        # 开始按钮
        self.start_btn = QPushButton("🚀 开始处理")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 18px; }")
        left_layout.addWidget(self.progress_bar)

        # 日志
        log_label = QLabel("📋 处理日志")
        log_label.setStyleSheet("font-weight: bold; margin-top: 2px;")
        left_layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px; background: #f8f9fa;")
        left_layout.addWidget(self.log_text)

        left_layout.addStretch()

        # ========== 右侧面板 ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        list_title = QLabel("📹 视频列表")
        list_title.setStyleSheet("font-size: 15px; font-weight: bold; padding: 4px 0;")
        right_layout.addWidget(list_title)

        self.video_table = VideoTableWidget(self)
        self.video_table.setMinimumHeight(450)
        right_layout.addWidget(self.video_table)

        drop_label = QLabel("💡 提示：拖拽视频文件到表格中添加 | 悬停缩略图预览 | 双击文件名重命名 | 双击行打开视频")
        drop_label.setStyleSheet("color: #999; font-size: 11px; padding: 4px;")
        drop_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(drop_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(line)

        self.stats_label = QLabel("就绪")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        right_layout.addWidget(self.stats_label)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        self.statusBar().showMessage("就绪")
        self.load_defaults()

    def load_defaults(self):
        default_folder = "/Users/leiliang/Desktop/movie_space"
        default_watermark = "/Users/leiliang/Desktop/movie_space/水印/shuiyin.png"

        if os.path.exists(default_folder):
            self.folder_input.setText(default_folder)
            self.video_table.load_videos(default_folder)
            self.update_stats()
        if os.path.exists(default_watermark):
            self.watermark_input.setText(default_watermark)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder:
            self.folder_input.setText(folder)
            self.video_table.load_videos(folder)
            self.update_stats()

    def select_watermark(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "",
            "图片 (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if file:
            self.watermark_input.setText(file)

    def update_stats(self):
        total = self.video_table.get_video_count()
        self.stats_label.setText(f"📊 共 {total} 个视频 | 每页 {PAGE_SIZE} 个")

    def on_mode_changed(self, index):
        self.count_spin.setEnabled(index == 1)

    def log(self, msg):
        self.log_text.append(msg)
        QApplication.processEvents()

    def on_video_status(self, filename, status):
        for i in range(self.video_table.rows_layout.count()):
            item = self.video_table.rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'filename'):
                if item.widget().filename == filename:
                    if status == 'processing':
                        item.widget().set_processing()
                    elif status == 'done':
                        item.widget().set_done()
                    elif status == 'error':
                        item.widget().set_error()
                    break

    def start_processing(self):
        input_folder = self.folder_input.text()
        watermark_path = self.watermark_input.text()

        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "错误", "视频文件夹不存在！")
            return

        if not os.path.exists(watermark_path):
            QMessageBox.warning(self, "错误", "水印图片不存在！")
            return

        mode_index = self.mode_combo.currentIndex()
        mode_names = ['selected', 'count', 'all']
        count_mode = mode_names[mode_index]

        selected_videos = self.video_table.get_selected_videos()

        if count_mode == 'selected' and not selected_videos:
            QMessageBox.warning(self, "提示", "请先在视频列表中选择要处理的视频！")
            return

        params = {
            'right_margin': self.margin_slider.value(),
            'bottom_y': self.y_slider.value(),
            'bounce_speed_x': self.speed_x_slider.value() / 100,
            'bounce_speed_y': self.speed_y_slider.value() / 100,
            'top_margin': self.top_slider.value(),
            'bottom_margin': self.bottom_slider.value(),
            'position_mode': self.wm_mode_combo.currentIndex() + 1,
        }

        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ 处理中...")
        self.log_text.clear()
        self.progress_bar.setValue(0)

        self.worker = WatermarkWorker(
            input_folder, watermark_path, params,
            video_list=selected_videos if count_mode == 'selected' else None,
            count_mode=count_mode,
            count=self.count_spin.value()
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.log)
        self.worker.video_status.connect(self.on_video_status)
        self.worker.start()

    def on_progress(self, value, msg):
        self.statusBar().showMessage(msg)

    def on_finished(self, success, msg):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 开始处理")
        self.progress_bar.setValue(100 if success else 0)
        self.statusBar().showMessage(msg)

        if success:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.warning(self, "错误", msg)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()