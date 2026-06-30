# config.py
"""全局配置常量 - 支持环境切换"""
import os
import json

# ================================================================
# 🌍 环境配置
# ================================================================
ENV = "production"  # "test" 或 "production"

# ================================================================
# 应用配置
# ================================================================
VERSION = "1.0.0"
PAGE_SIZE = 20

# 视频支持的扩展名
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}

# ================================================================
# FFmpeg 配置
# ================================================================
FFMPEG_DEFAULT_VIDEO_BITRATE = "4M"
FFMPEG_DEFAULT_AUDIO_BITRATE = "44k"
FFMPEG_DEFAULT_FPS = 30
FFMPEG_WATERMARK_SCALE = 200

# ================================================================
# 工具面板配置
# ================================================================
MAX_QUICK_TOOLS = 7
TOOL_CONFIG_FILE = "tool_config.json"

# ================================================================
# SMB 共享配置
# ================================================================
SMB_CONFIG = {
    "host": "192.168.6.148",
    "share_name": "运营素材",
    "username": "雷亮",
    "password": "Aa123456",
    "remote_path": "溯源视频",
    "domain": "",
    "port": 445,
}

# ================================================================
# 溯源配置
# ================================================================
TRACE_CONFIG = {
    "date_format": "%Y%m%d",
    "name_format": "{trace_code}_{date}_{editor_initials}_{operator_initials}.MP4",
}

# ================================================================
# 快手 API 配置
# ================================================================
KUAISHOU_APP_ID = 165929555
KUAISHOU_SECRET = '~O6#V7t&&@h7I?&?'
KUAISHOU_ACCESS_TOKEN = 'e3b4fc485155888b38d5a4bd4c16f579'
KUAISHOU_ADVERTISER_ID = 113788225
KUAISHOU_REFRESH_TOKEN = '99721782a35e903f43b18f6f7ac2a293'
KUAISHOU_AUTH_CODE = '我是你爷爷'

# ================================================================
# 数据库配置 - 根据环境切换
# ================================================================
if ENV == "test":
    DB_CFG = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "123456",
        "database": "yunying_test",
        "charset": "utf8mb4",
    }
else:
    DB_CFG = {
        "host": "rm-cn-5yd3eq34z000d37o.rwlb.rds.aliyuncs.com",
        "port": 3306,
        "user": "yunying",
        "password": "JvX0Z&kHHNk#6^0b(Up%",
        "database": "yunying_center",
        "charset": "utf8mb4"
    }

