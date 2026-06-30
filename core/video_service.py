# core/video_service.py
"""视频数据服务"""
import pymysql
from core.database import get_connection
# ... existing code ...


def get_operator_list():
    """获取操作员/用户列表"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT id, real_name FROM sys_user ORDER BY id ASC"
        cur.execute(sql)
        res = cur.fetchall()
        cur.close()
        return res
    finally:
        conn.close()

def get_user_video_list(user_id: int, is_admin: bool):
    """
    获取用户的视频列表

    Args:
        user_id: 用户ID
        is_admin: 是否为管理员

    Returns:
        list: 视频列表 [(trace_code, video_path, record_date, real_name), ...]
    """
    conn = get_connection()

    try:
        cur = conn.cursor()

        if is_admin:
            sql = """
            SELECT vt.trace_code, vt.video_path, vt.record_date, su.real_name
            FROM video_trace vt
            LEFT JOIN sys_user su ON vt.user_id = su.id
            ORDER BY vt.record_date DESC
            """
            cur.execute(sql)
        else:
            sql = """
            SELECT vt.trace_code, vt.video_path, vt.record_date, su.real_name
            FROM video_trace vt
            LEFT JOIN sys_user su ON vt.user_id = su.id
            WHERE vt.user_id=%s
            ORDER BY vt.record_date DESC
            """
            cur.execute(sql, (user_id,))

        result = cur.fetchall()
        cur.close()
        return result

    finally:
        conn.close()