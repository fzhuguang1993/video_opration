# services/kuaishou_sync.py
"""快手数据同步服务 - 重写版"""

import pymysql
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from utils.api.kuaishou_loader import KuaishouReportLoader
from config import DB_CFG


class KuaishouSyncService:
    """快手数据同步服务"""

    def __init__(self):
        self.loader = KuaishouReportLoader()

    def _is_valid(self, item: Dict) -> bool:
        """判断数据是否有效"""
        photo_id = item.get('photo_id')
        photo_name = item.get('photo_name', '')
        return bool(photo_id and photo_name and len(photo_name) >= 4)

    def _calc_metrics(self, item: Dict) -> Dict:
        """计算衍生指标"""
        show = item.get('show', 0)
        aclick = item.get('aclick', 0)
        bclick = item.get('bclick', 0)
        charge = item.get('charge', 0)
        conversion = item.get('conversion_num', 0)

        total_impression = show + aclick

        return {
            'total_impression': total_impression,
            # 点击率：百分比数值，保留2位小数
            'click_rate': round(bclick / total_impression * 100, 2) if total_impression > 0 else 0,
            # CPM：保留2位小数
            'cpm': round(charge / total_impression * 1000, 2) if total_impression > 0 else 0,
            # 转化率：百分比数值，保留2位小数
            'conversion_rate': round(conversion / bclick * 100, 2) if bclick > 0 else 0,
            # 转化成本：保留2位小数
            'conversion_cost': round(charge / conversion, 2) if conversion > 0 else 0,
        }

    def _calc_metrics(self, item: Dict) -> Dict:
        show = item.get('show', 0)
        aclick = item.get('aclick', 0)
        bclick = item.get('bclick', 0)
        charge = item.get('charge', 0)
        conversion = item.get('conversion_num', 0)

        total_impression = show + aclick

        return {
            'total_impression': total_impression,
            'click_rate': round(bclick / total_impression * 100, 2) if total_impression > 0 else 0,
            'cpm': round(charge / total_impression * 1000, 2) if total_impression > 0 else 0,
            'conversion_rate': round(conversion / bclick * 100, 2) if bclick > 0 else 0,
            'conversion_cost': round(charge / conversion, 2) if conversion > 0 else 0,
            'submit': item.get('submit', 0),  # ✅ 改成 'submit'
            'click_1k_cost': item.get('click1kCost', 0),
        }

    # services/kuaishou_sync.py

    # services/kuaishou_sync.py

    def _upsert_report(self, cursor, item: Dict, metrics: Dict, week_cost: float):
        sql = """
            INSERT INTO kuaishou_report_2026 (
                stat_date, photo_id, photo_name,
                impression_count, click_count, click_rate,
                total_cost, daily_cost, cpm_data,
                play_count, play_3s_count, play_5s_count, play_end_count,
                three_sec_rate, five_sec_rate, end_rate,
                like_count, comment_count, share_count, follow_count, unfollow_count,
                conversion_count, conversion_rate, conversion_cost,
                video_rating, week_cost
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                photo_name = VALUES(photo_name),
                impression_count = VALUES(impression_count),
                click_count = VALUES(click_count),
                click_rate = VALUES(click_rate),
                total_cost = VALUES(total_cost),
                daily_cost = VALUES(daily_cost),
                cpm_data = VALUES(cpm_data),
                play_count = VALUES(play_count),
                play_3s_count = VALUES(play_3s_count),
                play_5s_count = VALUES(play_5s_count),
                play_end_count = VALUES(play_end_count),
                three_sec_rate = VALUES(three_sec_rate),
                five_sec_rate = VALUES(five_sec_rate),
                end_rate = VALUES(end_rate),
                like_count = VALUES(like_count),
                comment_count = VALUES(comment_count),
                share_count = VALUES(share_count),
                follow_count = VALUES(follow_count),
                unfollow_count = VALUES(unfollow_count),
                conversion_count = VALUES(conversion_count),
                conversion_rate = VALUES(conversion_rate),
                conversion_cost = VALUES(conversion_cost),
                video_rating = VALUES(video_rating),
                week_cost = VALUES(week_cost),
                updated_at = NOW()
        """

        cursor.execute(sql, (
            item.get('stat_date'),
            item.get('photo_id'),
            item.get('photo_name', ''),
            metrics['total_impression'],
            item.get('bclick', 0),
            metrics['click_rate'],
            round(item.get('charge', 0), 2),
            round(item.get('charge', 0), 2),
            metrics['click_1k_cost'],  # ✅ cpm_data 字段存 click_1k_cost
            item.get('aclick', 0),
            item.get('played_three_seconds', 0),
            item.get('played_five_seconds', 0),
            item.get('played_end', 0),
            round(item.get('play_3s_ratio', 0) * 100, 2),
            round(item.get('play_5s_ratio', 0) * 100, 2),
            round(item.get('play_end_ratio', 0) * 100, 2),
            item.get('like', 0),
            item.get('comment', 0),
            item.get('share', 0),
            item.get('follow', 0),
            item.get('cancel_follow', 0),
            metrics['submit'],  # ✅ conversion_count 字段存 submit
            metrics['conversion_rate'],
            metrics['conversion_cost'],
            '',  # video_rating
            round(week_cost, 2)
        ))

    # services/kuaishou_sync.py

    def _upsert_video_stat(self, cursor, trace_code: str, item: Dict, metrics: Dict, week_cost: float):
        sql = """
            INSERT INTO video_stat (
                trace_code, total_cost, daily_cost, week_cost,
                impression_count, click_count, click_rate,
                conversion_count, conversion_rate, cpm_data,
                three_sec_rate, five_sec_rate, video_rating,
                stat_date, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                total_cost = VALUES(total_cost),
                daily_cost = VALUES(daily_cost),
                week_cost = VALUES(week_cost),
                impression_count = VALUES(impression_count),
                click_count = VALUES(click_count),
                click_rate = VALUES(click_rate),
                conversion_count = VALUES(conversion_count),
                conversion_rate = VALUES(conversion_rate),
                cpm_data = VALUES(cpm_data),
                three_sec_rate = VALUES(three_sec_rate),
                five_sec_rate = VALUES(five_sec_rate),
                video_rating = VALUES(video_rating),
                stat_date = VALUES(stat_date),
                updated_at = NOW()
        """

        cursor.execute(sql, (
            trace_code,
            round(item.get('charge', 0), 2),
            round(item.get('charge', 0), 2),
            round(week_cost, 2),
            metrics['total_impression'],
            item.get('bclick', 0),
            metrics['click_rate'],
            item.get('conversion_num', 0),
            metrics['conversion_rate'],
            metrics['cpm'],  # 这里还是用 cpm，不用 click_1k_cost
            round(item.get('play_3s_ratio', 0) * 100, 2),
            round(item.get('play_5s_ratio', 0) * 100, 2),
            '',
            item.get('stat_date')
        ))

    def _insert_orphan(self, cursor, photo_id: str, photo_name: str):
        """插入孤儿表"""
        sql = """
            INSERT INTO kuaishou_orphan_video (
                photo_id, photo_name, last_found_date, status
            ) VALUES (%s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE
                photo_name = VALUES(photo_name),
                last_found_date = VALUES(last_found_date),
                updated_at = NOW()
        """
        cursor.execute(sql, (
            photo_id,
            photo_name,
            datetime.now().strftime('%Y-%m-%d')
        ))

    def sync(self, target_date: Optional[str] = None, dry_run: bool = False) -> Dict:
        """执行数据同步"""
        if not target_date:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        result = {
            'target_date': target_date,
            'total': 0,
            'clean': 0,
            'dirty': 0,
            'matched': 0,
            'orphan': 0,
            'report_updated': 0,
            'success': False,
            'error': None
        }

        # 1. 获取数据
        data = self.loader.fetch_report_with_names(target_date, target_date)
        if not data:
            result['error'] = '无数据'
            return result

        result['total'] = len(data)

        # 2. 过滤有效数据
        clean_data = [item for item in data if self._is_valid(item)]
        result['dirty'] = len(data) - len(clean_data)
        result['clean'] = len(clean_data)

        if not clean_data:
            result['error'] = '无有效数据'
            return result

        if dry_run:
            result['success'] = True
            return result

        # 3. 计算周消耗
        week_start = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        week_data = self.loader.get_report(week_start, target_date)
        week_cost = sum(item.get('charge', 0) for item in week_data)

        # 4. 写入数据库
        conn = pymysql.connect(**DB_CFG)
        cursor = conn.cursor()

        try:
            for item in clean_data:
                photo_id = item.get('photo_id')
                photo_name = item.get('photo_name', '')
                trace_code = photo_name[:4] if len(photo_name) >= 4 else ''

                # 计算指标
                metrics = self._calc_metrics(item)

                # 写入日报表
                self._upsert_report(cursor, item, metrics, week_cost)
                result['report_updated'] += 1

                # 检查 video_stat 是否存在
                if trace_code:
                    cursor.execute("SELECT trace_code FROM video_stat WHERE trace_code = %s", (trace_code,))
                    exists = cursor.fetchone()

                    if exists:
                        self._upsert_video_stat(cursor, trace_code, item, metrics, week_cost)
                        result['matched'] += 1
                    else:
                        self._insert_orphan(cursor, photo_id, photo_name)
                        result['orphan'] += 1
                else:
                    self._insert_orphan(cursor, photo_id, photo_name)
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


def sync_kuaishou_data(date: Optional[str] = None) -> Dict:
    """同步快手数据（供按钮调用）"""
    service = KuaishouSyncService()
    return service.sync(date)


def sync_kuaishou_data_preview(date: Optional[str] = None) -> Dict:
    """预览快手数据（不写入）"""
    service = KuaishouSyncService()
    return service.sync(date, dry_run=True)