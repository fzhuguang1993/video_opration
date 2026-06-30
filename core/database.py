# core/database.py
"""数据库配置和连接管理 - 唯一数据库访问入口"""
from typing import Optional
import pymysql
from config import DB_CFG


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CFG)


def get_db_dict() -> dict:
    """获取数据库配置字典（供需要 **DB_CFG 的场景使用）"""
    return dict(DB_CFG)