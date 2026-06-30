# services/kuaishou_sync.py
"""快手数据同步服务 - 对齐 test 脚本逻辑"""

import pymysql
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from utils.api.kuaishou_loader import KuaishouReportLoader
from config import DB_CFG


class KuaishouSyncService:
    """快手数据同步服务"""

    def __init__(self):
        self.loader = KuaishouReportLoader()

    def _get_valid_trace_codes(self) -> set:
        """从 video_trace 表获取合法 trace_code 白名单"""
        conn = pymysql.connect(**DB_CFG)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT trace_code FROM video_trace")
            rows = cursor.fetchall()
            return set(row[0] for row in rows)
        except Exception as e:
            print(f"⚠️ 查询 video_trace 失败: {e}")
            return set()
        finally:
            cursor.close()
            conn.close()

    def _extract_trace_code(self, photo_name: str) -> str:
        if not photo_name:
            return ''
        return photo_name[:4] if len(photo_name) >= 4 else photo_name

    # services/kuaishou_sync.py - 修复 _map_to_stat 方法

    def _map_to_stat(self, report_item: Dict, video_info: Dict) -> Dict:
        """映射报表 + 视频详情 -> video_stat 字段"""
        charge = report_item.get('charge', 0) or 0
        aclick = report_item.get('aclick', 0) or 0
        submit = report_item.get('submit', 0) or 0

        return {
            'total_cost': charge,
            'daily_cost': charge,
            'week_cost': charge,
            'cover_impression': report_item.get('show', 0) or 0,
            'material_impression': aclick,
            'action_count': report_item.get('bclick', 0) or 0,
            'cover_click': report_item.get('photo_click', 0) or 0,
            'cover_click_rate': report_item.get('photo_click_ratio', 0) or 0,
            'impression_1k_cost': report_item.get('impression_1k_cost', 0) or 0,
            'click_1k_cost': report_item.get('click_1k_cost', 0) or 0,
            'photo_click_cost': report_item.get('photo_click_cost', 0) or 0,
            'action_cost': report_item.get('action_cost', 0) or 0,
            'action_rate': report_item.get('action_ratio', 0) or 0,
            'conversion_count': submit,
            'conversion_rate': round(submit / aclick, 4) if aclick > 0 else 0,
            'three_sec_rate': report_item.get('play_3s_ratio', 0) or 0,
            'five_sec_rate': report_item.get('play_5s_ratio', 0) or 0,
            'seventy_five_rate': report_item.get('ad_photo_played_75percent_ratio', 0) or 0,
            'end_rate': report_item.get('play_end_ratio', 0) or 0,
            # ✅ 关键修复：video_info 中字段名是 url 和 cover_url
            'photo_url': video_info.get('url', ''),  # 视频链接
            'cover_url': video_info.get('cover_url', ''),  # 封面链接
            'photo_name': video_info.get('photo_name', ''),  # 视频名称
        }

    def _upsert_video_stat(self, cursor, trace_code: str, stat: Dict, stat_date: str):
        sql = """
            INSERT INTO video_stat (
                trace_code,
                total_cost, daily_cost, week_cost,
                cover_impression, material_impression, action_count, cover_click,
                cover_click_rate, impression_1k_cost, click_1k_cost,
                photo_click_cost, action_cost, action_rate,
                conversion_count, conversion_rate,
                three_sec_rate, five_sec_rate, seventy_five_rate, end_rate,
                photo_url, cover_url,
                video_rating, stat_date
            ) VALUES (
                %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s
            ) ON DUPLICATE KEY UPDATE
                total_cost = VALUES(total_cost),
                daily_cost = VALUES(daily_cost),
                week_cost = VALUES(week_cost),
                cover_impression = VALUES(cover_impression),
                material_impression = VALUES(material_impression),
                action_count = VALUES(action_count),
                cover_click = VALUES(cover_click),
                cover_click_rate = VALUES(cover_click_rate),
                impression_1k_cost = VALUES(impression_1k_cost),
                click_1k_cost = VALUES(click_1k_cost),
                photo_click_cost = VALUES(photo_click_cost),
                action_cost = VALUES(action_cost),
                action_rate = VALUES(action_rate),
                conversion_count = VALUES(conversion_count),
                conversion_rate = VALUES(conversion_rate),
                three_sec_rate = VALUES(three_sec_rate),
                five_sec_rate = VALUES(five_sec_rate),
                seventy_five_rate = VALUES(seventy_five_rate),
                end_rate = VALUES(end_rate),
                photo_url = VALUES(photo_url),
                cover_url = VALUES(cover_url),
                video_rating = VALUES(video_rating),
                stat_date = VALUES(stat_date),
                updated_at = NOW()
        """
        cursor.execute(sql, (
            trace_code,
            stat['total_cost'], stat['daily_cost'], stat['week_cost'],
            stat['cover_impression'], stat['material_impression'], stat['action_count'],
            stat['cover_click'], stat['cover_click_rate'], stat['impression_1k_cost'],
            stat['click_1k_cost'], stat['photo_click_cost'], stat['action_cost'],
            stat['action_rate'], stat['conversion_count'], stat['conversion_rate'],
            stat['three_sec_rate'], stat['five_sec_rate'], stat['seventy_five_rate'],
            stat['end_rate'], stat['photo_url'], stat['cover_url'],
            '', stat_date
        ))

    def _insert_orphan(self, cursor, photo_id: str, photo_name: str, trace_code: str, stat_date: str):
        if not photo_name or not photo_name.strip():
            return

        cursor.execute("SELECT id FROM kuaishou_orphan_video WHERE photo_id = %s", (photo_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE kuaishou_orphan_video
                SET last_found_date = %s, updated_at = NOW()
                WHERE photo_id = %s
            """, (stat_date, photo_id))
        else:
            cursor.execute("""
                INSERT INTO kuaishou_orphan_video (
                    photo_id, photo_name, trace_code, last_found_date, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, 0, NOW(), NOW())
            """, (photo_id, photo_name, trace_code, stat_date))

    def sync(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
             target_date: Optional[str] = None, dry_run: bool = False) -> Dict:
        if target_date:
            start_date = target_date
            end_date = target_date

        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = start_date

        result = {
            'start_date': start_date,
            'end_date': end_date,
            'total': 0,
            'matched': 0,
            'orphan': 0,
            'dirty': 0,
            'success': False,
            'error': None
        }

        # 1. 获取白名单
        valid_codes = self._get_valid_trace_codes()

        # 2. 查报表
        report_data = self.loader.get_report(start_date, end_date)
        if not report_data:
            result['error'] = '无数据'
            return result
        result['total'] = len(report_data)

        # 3. 查视频详情
        photo_ids = [item.get('photo_id') for item in report_data if item.get('photo_id')]
        video_map = self.loader.get_video_details(photo_ids)

        if dry_run:
            result['success'] = True
            return result

        stat_date = report_data[0].get('stat_date', start_date)

        # 4. 映射 & 分流写入
        conn = pymysql.connect(**DB_CFG)
        cursor = conn.cursor()

        try:
            for item in report_data:
                photo_id = item.get('photo_id', '')
                video_info = video_map.get(photo_id, {})
                photo_name = video_info.get('photo_name', '')
                trace_code = self._extract_trace_code(photo_name)

                if not photo_name or not photo_name.strip():
                    result['dirty'] += 1
                    continue

                if trace_code and trace_code in valid_codes:
                    stat = self._map_to_stat(item, video_info)
                    self._upsert_video_stat(cursor, trace_code, stat, stat_date)
                    result['matched'] += 1
                else:
                    self._insert_orphan(cursor, photo_id, photo_name, trace_code, stat_date)
                    result['orphan'] += 1

            conn.commit()
            result['success'] = True

        except Exception as e:
            conn.rollback()
            result['error'] = str(e)
            raise
        finally:
            cursor.close()
            conn.close()

        return result


def sync_kuaishou_data(start_date: Optional[str] = None, end_date: Optional[str] = None,
                       date: Optional[str] = None) -> Dict:
    service = KuaishouSyncService()
    return service.sync(start_date=start_date, end_date=end_date, target_date=date)


def sync_kuaishou_data_preview(start_date: Optional[str] = None, end_date: Optional[str] = None,
                               date: Optional[str] = None) -> Dict:
    service = KuaishouSyncService()
    return service.sync(start_date=start_date, end_date=end_date, target_date=date, dry_run=True)
