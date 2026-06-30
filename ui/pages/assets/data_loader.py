# ui/pages/assets/data_loader.py
"""资产管理 - 数据加载"""
from config import DB_CFG
import pymysql
from core.logger import get_logger

class AssetsDataLoader:
    """资产管理数据加载器"""

    def __init__(self, user_id=None, user_role=0):
        self.logger = get_logger("assets_data_loader")
        self.user_id = user_id
        self.user_role = user_role

    def is_admin(self) -> bool:
        return self.user_role == 1

    def load_editors(self) -> list:
        conn = pymysql.connect(**DB_CFG)
        cur = conn.cursor()
        cur.execute("SELECT id, real_name FROM sys_user WHERE role = 3 ORDER BY real_name")
        editors = cur.fetchall()
        cur.close()
        conn.close()
        return editors

    def load_raw_data(self) -> list:
        conn = pymysql.connect(**DB_CFG)
        cur = conn.cursor()

        where_clause = ""
        if not self.is_admin():
            if self.user_role == 3:
                where_clause = f"WHERE vt.user_id = {int(self.user_id)}"
            elif self.user_role == 2:
                where_clause = f"WHERE vt.operator_id = {int(self.user_id)}"
            else:
                where_clause = "WHERE 1=0"

        cur.execute(f"""
            SELECT vt.id, vt.trace_code, vt.video_path, vt.record_date,
                   editor.real_name, operator.real_name, vt.user_id, vt.operator_id
            FROM video_trace vt
            LEFT JOIN sys_user editor ON vt.user_id = editor.id
            LEFT JOIN sys_user operator ON vt.operator_id = operator.id
            {where_clause}
            ORDER BY vt.record_date DESC
        """)
        raw_data = cur.fetchall()

        cur.execute("SELECT trace_code, bind_trace_code FROM video_bind")
        all_binds = cur.fetchall()
        cur.close()
        conn.close()

        return raw_data, all_binds

    def build_trace_lookup(self, raw_data: list) -> dict:
        lookup = {}
        for row in raw_data:
            lookup[row[1]] = {
                "id": row[0], "trace_code": row[1], "video_path": row[2],
                "record_date": row[3], "editor_name": row[4] or "-",
                "operator_name": row[5] or "-", "user_id": row[6], "operator_id": row[7],
            }
        return lookup

    def build_bind_map(self, all_binds: list):
        bind_map = {}
        child_codes = set()
        for child_code, parent_code in all_binds:
            bind_map.setdefault(parent_code, []).append(child_code)
            child_codes.add(child_code)
        return bind_map, child_codes

    def build_all_data(self, raw_data: list, child_codes: set, bind_map: dict) -> list:
        result = []
        for row in raw_data:
            tc = row[1]
            if tc in child_codes:
                continue
            result.append({
                "id": row[0], "trace_code": tc, "video_path": row[2],
                "record_date": row[3], "editor_name": row[4] or "-",
                "operator_name": row[5] or "-", "user_id": row[6], "operator_id": row[7],
                "is_host": tc in bind_map,
                "children": bind_map.get(tc, []),
            })
        return result

    def load_stat_data(self, trace_codes: list) -> dict:
        if not trace_codes:
            return {}

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            placeholders = ",".join(["%s"] * len(trace_codes))
            cur.execute(f"""
                SELECT trace_code, total_cost, daily_cost, week_cost,
                       cover_impression, material_impression, action_count, cover_click,
                       cover_click_rate, impression_1k_cost, click_1k_cost,
                       photo_click_cost, action_cost, action_rate,
                       conversion_count, conversion_rate,
                       three_sec_rate, five_sec_rate, seventy_five_rate, end_rate,
                       video_rating, photo_url, cover_url
                FROM video_stat
                WHERE trace_code COLLATE utf8mb4_unicode_ci IN ({placeholders})
            """, trace_codes)

            stat_map = {}
            for row in cur.fetchall():
                stat_map[row[0]] = {
                    "total_cost": row[1], "daily_cost": row[2], "week_cost": row[3],
                    "cover_impression": row[4], "material_impression": row[5],
                    "action_count": row[6], "cover_click": row[7],
                    "cover_click_rate": row[8], "impression_1k_cost": row[9],
                    "click_1k_cost": row[10], "photo_click_cost": row[11],
                    "action_cost": row[12], "action_rate": row[13],
                    "conversion_count": row[14], "conversion_rate": row[15],
                    "three_sec_rate": row[16], "five_sec_rate": row[17],
                    "seventy_five_rate": row[18], "end_rate": row[19],
                    "video_rating": row[20], "photo_url": row[21], "cover_url": row[22],
                }
            cur.close()
            conn.close()
            return stat_map
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}")
            return {}
