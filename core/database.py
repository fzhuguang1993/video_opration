# core/database.py
"""数据库配置和连接管理"""
from dataclasses import dataclass
from typing import Optional
import pymysql


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "rm-cn-5yd3eq34z000d37o.rwlb.rds.aliyuncs.com"
    port: int = 3306
    user: str = "yunying"
    password: str = "JvX0Z&kHHNk#6^0b(Up%"
    database: str = "yunying_center"
    charset: str = "utf8mb4"

    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset
        )


# 单例
_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config