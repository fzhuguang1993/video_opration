import os
import ffmpeg
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import random

# --- 配置参数 ---
INPUT_FOLDER = "/Users/leiliang/Desktop/movie_space"
WATERMARK_FOLDER = "/Users/leiliang/Desktop/movie_space/水印"
TARGET_FPS = 30
VIDEO_BITRATE = "4M"
AUDIO_BITRATE = "44k"
ASPECT_RATIO = "9:16"
# -----------------

VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}


def get_target_dimensions(ratio):
    if ratio == "9:16":
        return 1080, 1920
    elif ratio == "9:19":
        return 1080, 2280
    elif ratio == "16:9":
        return 1920, 1080
    else:
        return 1080, 1920


def check_video_info(file_path):
    """检查视频文件的详细信息"""
    try:
        probe = ffmpeg.probe(file_path)
        print(f"\n📊 文件信息: {os.path.basename(file_path)}")

        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                width = stream.get('width', 'N/A')
                height = stream.get('height', 'N/A')
                print(f"   🎬 视频: {stream.get('codec_name', 'N/A')}")
                print(f"      分辨率: {width}x{height}")
                if width != 'N/A' and height != 'N/A':
                    ratio = width / height
                    print(f"      宽高比: {ratio:.3f}")
                print(f"      帧率: {stream.get('r_frame_rate', 'N/A')}")
                print(f"      旋转: {stream.get('rotate', '0')}")
                if 'bit_rate' in stream:
                    print(f"      码率: {int(stream['bit_rate']) / 1000:.0f} kbps")

            elif stream['codec_type'] == 'audio':
                print(f"   🔊 音频: {stream.get('codec_name', 'N/A')}")
                print(f"      采样率: {stream.get('sample_rate', 'N/A')} Hz")
                print(f"      声道: {stream.get('channels', 'N/A')}")
                if 'bit_rate' in stream:
                    print(f"      码率: {int(stream['bit_rate']) / 1000:.0f} kbps")

        print(f"   📦 文件大小: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
        print("-" * 40)
    except Exception as e:
        print(f"  ⚠️ 无法读取文件信息: {e}")


def get_video_list(folder_path):
    """获取文件夹中所有视频文件"""
    video_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        ext = Path(filename).suffix.lower()
        if ext in VIDEO_EXTS:
            video_files.append(filename)
    return sorted(video_files)


def get_watermark_position_choice():
    """交互式选择水印位置"""
    print("\n" + "=" * 60)
    print("🖼️  水印位置选择")
    print("=" * 60)
    print("  1. 右下角 (固定)")
    print("  2. 🔄 碰撞反弹 (全屏移动)")
    print("  3. 🎬 同时显示 (右下角 + 碰撞反弹)")
    print("=" * 60)

    while True:
        try:
            choice = input("请选择水印位置 (1-3): ").strip()
            choice = int(choice)
            if 1 <= choice <= 3:
                return choice
            else:
                print("⚠️ 请输入 1-3 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")


def get_position_name(position_choice):
    """获取位置名称（用于文件名）"""
    pos_names = {
        1: '右下角',
        2: '碰撞反弹',
        3: '右下角+碰撞反弹'
    }
    return pos_names.get(position_choice, f'位置{position_choice}')


def build_complex_filter(target_width, target_height, position_choice):
    """
    构建复杂滤镜（只支持图片水印）
    """
    # ============================================================
    # 🔧 水印位置调试参数（竖屏 1080x1920）
    # ============================================================
    # 右下角固定位置
    RIGHT_MARGIN = 148  # 右侧留白（从右边框往左数）调大 → 水印左移，调小 → 水印右移
    BOTTOM_Y = 1602  # 垂直位置（从顶部往下数）调大 → 水印下移，调小 → 水印上移

    # 碰撞反弹速度（数字越小越慢）
    BOUNCE_SPEED_X = 0.1  # 左右移动速度
    BOUNCE_SPEED_Y = 0.2  # 上下移动速度

    # 碰撞反弹滚动边界（上下各预留多少像素不滚动）
    BOUNCE_TOP_MARGIN = 250  # 顶部预留区域（水印不会进入）
    BOUNCE_BOTTOM_MARGIN = 250  # 底部预留区域（水印不会进入）
    # ============================================================

    # 水印尺寸
    wm_w = 200
    wm_h = 200

    filter_parts = []

    # 1. 视频流处理：缩放 + 填充
    filter_parts.append(
        f"[0:v]scale={target_width}:{target_height}:flags=lanczos,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black,format=rgb24[bg]"
    )

    if position_choice == 1:
        # 仅右下角固定
        filter_parts.append(f"[1:v]scale=200:-1:flags=lanczos,format=rgba[wm]")
        pos = f"W-{wm_w}-{RIGHT_MARGIN}:{BOTTOM_Y}"
        filter_parts.append(f"[bg][wm]overlay={pos}:alpha=1[out]")
        print(f"   🖼️  图片水印: 右下角 (固定) [右:{RIGHT_MARGIN}px, 下:{BOTTOM_Y}px]")

    elif position_choice == 2:
        # 仅碰撞反弹（限制滚动区域）
        filter_parts.append(f"[1:v]scale=200:-1:flags=lanczos,format=rgba[wm]")
        # 计算可滚动范围：顶部预留 BOUNCE_TOP_MARGIN，底部预留 BOUNCE_BOTTOM_MARGIN
        # 水印在垂直方向的活动范围：从 BOUNCE_TOP_MARGIN 到 (H - wm_h - BOUNCE_BOTTOM_MARGIN)
        scroll_range_y = f"(H - {wm_h} - {BOUNCE_TOP_MARGIN} - {BOUNCE_BOTTOM_MARGIN})"
        # 水印在水平方向的活动范围：从 0 到 (W - wm_w)
        scroll_range_x = f"(W - {wm_w})"

        filter_parts.append(
            f"[bg][wm]overlay=x='{scroll_range_x} * abs(sin(t*{BOUNCE_SPEED_X}))':y='{BOUNCE_TOP_MARGIN} + {scroll_range_y} * abs(cos(t*{BOUNCE_SPEED_Y}))':alpha=1[out]"
        )
        print(f"   🔄 碰撞反弹模式 (全屏移动) [上下预留:{BOUNCE_TOP_MARGIN}px/{BOUNCE_BOTTOM_MARGIN}px]")

    else:
        # 同时显示：右下角固定 + 碰撞反弹（限制滚动区域）
        filter_parts.append(f"[1:v]scale=200:-1:flags=lanczos,format=rgba[wm1]")
        filter_parts.append(f"[1:v]scale=200:-1:flags=lanczos,format=rgba[wm2]")

        # 右下角固定
        pos_fixed = f"W-{wm_w}-{RIGHT_MARGIN}:{BOTTOM_Y}"

        # 碰撞反弹 - 限制滚动区域
        scroll_range_y = f"(H - {wm_h} - {BOUNCE_TOP_MARGIN} - {BOUNCE_BOTTOM_MARGIN})"
        scroll_range_x = f"(W - {wm_w})"
        pos_bounce_x = f"{scroll_range_x} * abs(sin(t*{BOUNCE_SPEED_X}))"
        pos_bounce_y = f"{BOUNCE_TOP_MARGIN} + {scroll_range_y} * abs(cos(t*{BOUNCE_SPEED_Y}))"

        # 先叠加固定水印，再叠加反弹水印
        filter_parts.append(
            f"[bg][wm1]overlay={pos_fixed}:alpha=1[bg_with_fixed]"
        )
        filter_parts.append(
            f"[bg_with_fixed][wm2]overlay=x={pos_bounce_x}:y={pos_bounce_y}:alpha=1[out]"
        )
        print(
            f"   🖼️  右下角固定 + 🔄 碰撞反弹 (同时显示) [滚动区域上下各预留:{BOUNCE_TOP_MARGIN}px/{BOUNCE_BOTTOM_MARGIN}px]")

    complex_filter = ";".join(filter_parts)
    return complex_filter


def process_video(input_path, output_path, position_choice, image_path):
    """
    处理视频：图片水印
    """
    try:
        target_width, target_height = get_target_dimensions(ASPECT_RATIO)

        # 构建复杂滤镜
        complex_filter = build_complex_filter(
            target_width, target_height,
            position_choice
        )

        # 构建 FFmpeg 命令
        cmd = ['ffmpeg', '-i', input_path]

        # 添加图片水印
        if image_path and os.path.exists(image_path):
            cmd.extend(['-i', image_path])

        cmd.extend([
            '-filter_complex', complex_filter,
            '-map', '[out]',
            '-map', '0:a?',
            '-r', str(TARGET_FPS),
            '-c:v', 'libx264',
            '-b:v', VIDEO_BITRATE,
            '-preset', 'medium',
            '-metadata:s:v:0', 'rotate=0',
            '-aspect', f'{target_width}:{target_height}',
            '-sar', '1:1',
            '-c:a', 'aac',
            '-b:a', AUDIO_BITRATE,
            '-y', output_path
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ❌ FFmpeg错误:\n{result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 未知错误: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("🎬 视频格式转换工具 (图片水印版)")
    print("=" * 60)

    # 检查输入文件夹
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ 错误：输入文件夹不存在 -> {INPUT_FOLDER}")
        return

    # 检查水印图片
    image_path = os.path.join(WATERMARK_FOLDER, "shuiyin.png")
    if not os.path.exists(image_path):
        print(f"❌ 错误：水印图片不存在 -> {image_path}")
        print("   请确保水印文件夹中有 shuiyin.png")
        return

    print(f"\n✅ 找到水印图片: {image_path}")

    # 选择水印位置
    position_choice = get_watermark_position_choice()

    # 获取所有视频文件
    video_list = get_video_list(INPUT_FOLDER)

    if not video_list:
        print("❌ 文件夹中没有找到视频文件！")
        print(f"   支持的格式: {', '.join(sorted(VIDEO_EXTS))}")
        return

    # 显示视频列表
    print(f"\n📂 输入文件夹: {INPUT_FOLDER}")
    print(f"\n📹 找到 {len(video_list)} 个视频文件：")
    print("-" * 60)
    for i, video in enumerate(video_list, 1):
        file_path = os.path.join(INPUT_FOLDER, video)
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  {i:3d}. {video} ({file_size:.2f} MB)")
    print("-" * 60)

    # 用户确认
    print(f"\n⚙️  转换参数:")
    print(f"   📐 目标比例: {ASPECT_RATIO}")
    print(f"   🎞️  帧率: {TARGET_FPS} fps")
    print(f"   📹 视频码率: {VIDEO_BITRATE}")
    print(f"   🔊 音频码率: {AUDIO_BITRATE}")
    print(f"   🖼️  水印: shuiyin.png")

    pos_names = {1: '右下角 (固定)', 2: '🔄 碰撞反弹', 3: '右下角 + 碰撞反弹 (同时)'}
    print(f"   📍 位置: {pos_names.get(position_choice, '未知')}")

    print(f"   📂 目标文件夹: 在 {INPUT_FOLDER} 内创建")
    print("-" * 60)

    # 询问要处理多少个
    while True:
        try:
            user_input = input(f"\n请输入要处理的视频数量 (1-{len(video_list)}，输入 0 取消): ").strip()
            count = int(user_input)

            if count == 0:
                print("❌ 已取消操作")
                return
            elif 1 <= count <= len(video_list):
                break
            else:
                print(f"⚠️ 请输入 1 到 {len(video_list)} 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")

    # 确认开始
    print(f"\n📋 即将处理前 {count} 个视频，每个视频生成 1 个文件")
    confirm = input("确认开始转换？(y/n): ").strip().lower()

    if confirm != 'y' and confirm != 'yes':
        print("❌ 已取消操作")
        return

    # 创建输出文件夹
    today = datetime.now().strftime("%Y-%m-%d")
    output_folder_name = f"{today}_视频格式转换"
    output_folder = os.path.join(INPUT_FOLDER, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n📁 输出文件夹: {output_folder}")
    print("=" * 60)

    # 开始处理
    success_count = 0
    fail_count = 0
    failed_files = []

    for i in range(count):
        video_name = video_list[i]
        input_path = os.path.join(INPUT_FOLDER, video_name)
        video_base_name = Path(video_name).stem

        # 获取位置名称
        pos_name = get_position_name(position_choice)

        # 生成输出文件名
        output_filename = f"{today}_{video_base_name}_水印_{pos_name}.mp4"
        output_path = os.path.join(output_folder, output_filename)

        print(f"\n[{i+1}/{count}] 正在处理: {video_name}")
        print(f"   📤 输出: {output_filename}")
        print(f"   📍 位置: {pos_name}")

        success = process_video(
            input_path, output_path,
            position_choice, image_path
        )

        if success:
            success_count += 1
            print(f"   ✅ 成功")
        else:
            fail_count += 1
            failed_files.append(output_filename)
            print(f"   ❌ 失败")

    # 显示结果统计
    print("\n" + "=" * 60)
    print("📊 处理完成！")
    print(f"   ✅ 成功: {success_count} 个")
    print(f"   ❌ 失败: {fail_count} 个")

    if failed_files:
        print(f"\n❌ 失败的文件列表：")
        for file in failed_files:
            print(f"   - {file}")

    print(f"\n📁 输出文件夹: {output_folder}")

    if success_count > 0:
        open_folder = input(f"\n是否打开输出文件夹？(y/n): ").strip().lower()
        if open_folder == 'y' or open_folder == 'yes':
            try:
                subprocess.run(['open', output_folder])
                print("✅ 已打开文件夹")
            except:
                print(f"⚠️ 无法自动打开，请手动打开: {output_folder}")

    print("=" * 60)


if __name__ == "__main__":
    main()