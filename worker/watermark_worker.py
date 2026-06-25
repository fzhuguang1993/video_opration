# worker/watermark_worker.py
"""水印处理后台线程 - PySide6 版本"""
import os
import subprocess
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from utils.ffmpeg_utils import (
    build_watermark_command, generate_output_filename, get_ffmpeg_path
)
from utils.file_utils import get_sorted_video_files


class WatermarkWorker(QThread):
    """水印处理后台线程"""

    # PySide6 使用 Signal 替代 Signal
    progress = Signal(int, str)  # 进度(当前索引, 消息)
    finished = Signal(bool, str)  # 完成(是否成功, 消息)
    log = Signal(str)  # 日志消息
    video_status = Signal(str, str)  # 视频状态(文件名, 状态: processing/done/error)

    def __init__(self, input_folder: str, watermark_path: str, params: dict,
                 video_list: list = None, count_mode: str = 'all', count: int = 1,
                 operator_id: int = None):
        """
        初始化水印处理工作线程

        Args:
            input_folder: 输入文件夹路径
            watermark_path: 水印图片路径
            params: 处理参数
            video_list: 要处理的视频列表
            count_mode: 计数模式 ('all' 或 'count')
            count: 处理数量
            operator_id: 运营人员ID（可选）
        """
        super().__init__()
        self.input_folder = input_folder
        self.watermark_path = watermark_path
        self.params = params
        self.video_list = video_list or []
        self.count_mode = count_mode
        self.count = count
        self.operator_id = operator_id
        self._is_running = True

    def stop(self):
        """停止线程"""
        self._is_running = False

    def run(self):
        """线程执行逻辑"""
        try:
            # 确定要处理的视频列表
            if self.video_list:
                videos_to_process = self.video_list
            else:
                all_videos = get_sorted_video_files(self.input_folder)
                if self.count_mode == 'count':
                    videos_to_process = all_videos[:self.count]
                else:
                    videos_to_process = all_videos

            if not videos_to_process:
                self.finished.emit(False, "没有可处理的视频！")
                return

            self.log.emit(f"📹 共 {len(videos_to_process)} 个视频待处理")

            # 提取参数
            right_margin = self.params.get('right_margin', 148)
            bottom_y = self.params.get('bottom_y', 1602)
            bounce_speed_x = self.params.get('bounce_speed_x', 0.05)
            bounce_speed_y = self.params.get('bounce_speed_y', 0.05)
            top_margin = self.params.get('top_margin', 50)
            bottom_margin = self.params.get('bottom_margin', 50)
            position_mode = self.params.get('position_mode', 1)  # 1:右下角, 2:碰撞反弹, 3:同时

            total = len(videos_to_process)
            success_count = 0

            # 处理每个视频
            for i, video_path in enumerate(videos_to_process):
                if not self._is_running:
                    self.log.emit("⚠️ 用户中断处理")
                    break

                # 兼容绝对路径/相对路径
                if os.path.isabs(video_path):
                    input_path = video_path
                    video_name = Path(video_path).name
                else:
                    input_path = os.path.join(self.input_folder, video_path)
                    video_name = video_path

                if not os.path.exists(input_path):
                    self.log.emit(f"  ⚠️ 文件不存在: {video_name}")
                    self.video_status.emit(video_name, 'error')
                    continue

                # 更新状态为处理中
                self.video_status.emit(video_name, 'processing')

                # 生成输出路径
                output_name = generate_output_filename(input_path, position_mode)
                output_path = os.path.join(self.input_folder, output_name)

                # 发送进度
                self.progress.emit(i + 1, f"处理中: {video_name}")
                self.log.emit(f"\n[{i + 1}/{total}] {video_name}")

                # 构建FFmpeg命令
                cmd = build_watermark_command(
                    input_path, output_path, self.watermark_path,
                    right_margin, bottom_y,
                    bounce_speed_x, bounce_speed_y,
                    top_margin, bottom_margin,
                    position_mode
                )

                # 执行命令
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3600  # 1小时超时
                    )

                    # 处理结果
                    if result.returncode == 0:
                        success_count += 1
                        self.video_status.emit(video_name, 'done')
                        self.log.emit(f"  ✅ 成功: {output_name}")
                    else:
                        self.video_status.emit(video_name, 'error')
                        error_msg = result.stderr[:300] if result.stderr else "未知错误"
                        self.log.emit(f"  ❌ 失败: {error_msg}")

                except subprocess.TimeoutExpired:
                    self.video_status.emit(video_name, 'error')
                    self.log.emit(f"  ❌ 超时: {video_name} 处理超时（超过1小时）")
                except Exception as e:
                    self.video_status.emit(video_name, 'error')
                    self.log.emit(f"  ❌ 异常: {str(e)}")

            # 处理完成
            self.progress.emit(total, "完成")
            if success_count == total:
                msg = f"🎉 全部处理完成！成功: {success_count}/{total}"
            else:
                msg = f"⚠️ 处理完成，成功: {success_count}/{total}，失败: {total - success_count}"
            self.finished.emit(True, msg)

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.log.emit(f"❌ 严重错误: {error_msg}")
            self.finished.emit(False, f"错误: {str(e)}")

    def get_operator_id(self) -> int:
        """获取运营人员ID"""
        return self.operator_id