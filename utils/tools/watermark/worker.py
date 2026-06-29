"""水印处理后台线程"""

import os
import subprocess
from PySide6.QtCore import QThread, Signal

from utils.ffmpeg_utils import build_watermark_command, get_ffmpeg_path


class WatermarkWorker(QThread):
    """水印处理后台线程"""

    progress = Signal(int, int, str)
    finished = Signal(bool, str)
    log = Signal(str)

    def __init__(self, video_paths: list, watermark_path: str, params: dict):
        super().__init__()
        self.video_paths = video_paths
        self.watermark_path = watermark_path
        self.params = params
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        total = len(self.video_paths)
        success_count = 0
        fail_count = 0

        # 检查 FFmpeg 是否可用
        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            self.finished.emit(False, "FFmpeg 不可用，请检查安装")
            return

        # 检查水印文件是否存在
        if not os.path.exists(self.watermark_path):
            self.finished.emit(False, f"水印图片不存在: 仅处理视频格式")
            return

        # 提取参数
        mode = self.params.get('mode', 1)
        right_margin = self.params.get('right_margin', 148)
        bottom_y = self.params.get('bottom_y', 1602)
        speed_x = self.params.get('speed_x', 0.05)
        speed_y = self.params.get('speed_y', 0.05)
        top_margin = self.params.get('top_margin', 50)
        bottom_margin = self.params.get('bottom_margin', 50)

        for idx, video_path in enumerate(self.video_paths, 1):
            if not self._is_running:
                self.log.emit("⚠️ 用户中断")
                break

            self.progress.emit(idx, total, os.path.basename(video_path))
            self.log.emit(f"📹 处理: {os.path.basename(video_path)}")

            # 生成输出文件名
            dir_path = os.path.dirname(video_path)
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_name = f"{base_name}_水印_{mode}.mp4"
            output_path = os.path.join(dir_path, output_name)

            # 如果输出文件已存在，跳过
            if os.path.exists(output_path):
                self.log.emit(f"  ⚠️ 跳过: {output_name} 已存在")
                fail_count += 1
                continue

            # 构建命令
            cmd = build_watermark_command(
                video_path,
                output_path,
                self.watermark_path,
                right_margin,
                bottom_y,
                speed_x,
                speed_y,
                top_margin,
                bottom_margin,
                mode
            )

            try:
                self.log.emit(f"  🎬 执行 FFmpeg...")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1小时超时
                )

                if result.returncode == 0:
                    self.log.emit(f"  ✅ 成功: {output_name}")
                    success_count += 1
                else:
                    error_msg = result.stderr[:200] if result.stderr else "未知错误"
                    self.log.emit(f"  ❌ 失败: {error_msg}")
                    fail_count += 1

            except subprocess.TimeoutExpired:
                self.log.emit(f"  ❌ 超时: 处理超过1小时")
                fail_count += 1
            except Exception as e:
                self.log.emit(f"  ❌ 异常: {str(e)}")
                fail_count += 1

        msg = f"处理完成！成功: {success_count}，失败: {fail_count}"
        self.finished.emit(success_count > 0, msg)