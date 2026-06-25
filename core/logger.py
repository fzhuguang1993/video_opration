# core/logger.py
"""日志管理模块"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
        name: str = "movie_app",
        log_dir: str = "logs",
        level: int = logging.DEBUG,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
) -> logging.Logger:
    """
    设置日志系统

    Args:
        name: 日志名称
        log_dir: 日志目录
        level: 日志级别
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量

    Returns:
        配置好的Logger对象
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 创建Logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果已经有处理器，先清除（避免重复）
    if logger.handlers:
        logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器（带轮转）
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器（只显示INFO及以上）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 错误日志单独记录
    error_log_file = log_path / f"{name}_error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# 全局Logger实例
_default_logger: logging.Logger = None


def get_logger(name: str = None) -> logging.Logger:
    """获取全局Logger"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger(name or "movie_app")
    return _default_logger