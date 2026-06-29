# utils/api/kuaishou_loader.py
"""快手API接口封装 - 只刷新一次"""

import time
import requests
from typing import List, Dict

from config import KUAISHOU_ACCESS_TOKEN, KUAISHOU_ADVERTISER_ID
from utils.api.token_refresh import refresh_kuaishou_token


class KuaishouReportLoader:
    """快手日报表加载器"""

    def __init__(self):
        # 初始化时刷新一次 token
        print('🔄 初始化，获取最新 Token...')
        new_token, _ = refresh_kuaishou_token()
        if new_token:
            self.access_token = new_token
            from config import KUAISHOU_ADVERTISER_ID as adv_id
            self.advertiser_id = adv_id
            print(f'✅ Token 已初始化')
        else:
            self.access_token = KUAISHOU_ACCESS_TOKEN
            self.advertiser_id = KUAISHOU_ADVERTISER_ID
        self.BATCH_SIZE = 100

    # ================================================================
    # 1. 获取报表数据
    # ================================================================
    def get_report(self, start_date: str, end_date: str) -> List[Dict]:
        """获取素材报表数据"""
        url = 'https://ad.e.kuaishou.com/rest/openapi/v1/report/material_report'
        all_data = []
        page = 1

        while True:
            payload = {
                'advertiser_id': self.advertiser_id,
                'start_date': start_date,
                'end_date': end_date,
                'view_type': 5,
                'temporal_granularity': 'DAILY',
                'page': page,
                'page_size': self.BATCH_SIZE,
                'select_columns': [
                    'stat_date', 'photo_id', 'photo_name',
                    'totalCharge', 'impression', 'click',
                    'actionbarClick', 'actionRatio',
                    'play3sRatio', 'play5sRatio', 'playEndRatio',
                    'adPhotoPlayed75percentRatio',
                    'like', 'comment', 'share', 'follow', 'unfollow',
                    'conversion', 'formCount','conversionNumByImpression7d','click1kCost'
                ]
            }
            headers = {
                'Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'code' in data and data.get('code') != 0:
                    print(f'⚠️ API错误: {data.get("code")} - {data.get("msg")}')
                    break

                details = data.get('details', [])
                if not details:
                    break

                all_data.extend(details)

                if len(details) < self.BATCH_SIZE:
                    break

                page += 1

            except Exception as e:
                print(f'⚠️ 请求失败: {e}')
                break

        return all_data

    # ================================================================
    # 2. 获取视频名称
    # ================================================================
    def get_video_names(self, photo_ids: List[str]) -> Dict[str, str]:
        """批量获取视频名称"""
        unique_ids = list(set([pid for pid in photo_ids if pid]))
        if not unique_ids:
            return {}

        url = 'https://ad.e.kuaishou.com/rest/openapi/v1/file/ad/video/get'
        name_map = {}

        for i in range(0, len(unique_ids), 100):
            batch = unique_ids[i:i + 100]
            payload = {
                'advertiser_id': self.advertiser_id,
                'photo_ids': batch
            }
            headers = {
                'Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()

                    if data.get('code') == 0:
                        video_list = data.get('data', [])
                        for v in video_list:
                            pid = v.get('photo_id')
                            name_map[pid] = v.get('photo_name', '')
            except Exception as e:
                print(f'⚠️ 获取视频名称失败: {e}')
                continue

            time.sleep(0.3)

        return name_map

    # ================================================================
    # 3. 合并数据 - 返回最终结果
    # ================================================================
    def fetch_report_with_names(self, start_date: str, end_date: str) -> List[Dict]:
        """获取含视频名称的完整报表"""
        report_data = self.get_report(start_date, end_date)
        if not report_data:
            return []

        photo_ids = [item.get('photo_id') for item in report_data if item.get('photo_id')]
        name_map = self.get_video_names(photo_ids)

        result = []
        for item in report_data:
            photo_id = item.get('photo_id')
            photo_name = name_map.get(photo_id, '')
            item['photo_name'] = photo_name
            result.append(item)

        return result