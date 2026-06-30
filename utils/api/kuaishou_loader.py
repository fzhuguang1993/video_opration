# utils/api/kuaishou_loader.py
"""快手API加载器 - 统一管理快手API调用"""

import requests
from typing import List, Dict, Optional
from config import KUAISHOU_ACCESS_TOKEN, KUAISHOU_ADVERTISER_ID

BASE_URL = 'https://ad.e.kuaishou.com/rest/openapi/v1'


class KuaishouReportLoader:
    """快手报表数据加载器"""

    def __init__(self):
        self.headers = {
            'Access-Token': KUAISHOU_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        self.advertiser_id = KUAISHOU_ADVERTISER_ID

    def get_report(self, start_date: str, end_date: str, page_size: int = 100) -> List[Dict]:
        """获取素材报表数据"""
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
                'page_size': page_size,
                'select_columns': [
                    'stat_date', 'photo_id', 'photo_name',
                    'totalCharge', 'impression', 'click',
                    'actionbarClick', 'actionRatio',
                    'play3sRatio', 'play5sRatio', 'playEndRatio',
                    'adPhotoPlayed75percentRatio',
                    'like', 'comment', 'share', 'follow', 'unfollow',
                    'conversion', 'formCount',
                ]
            }

            try:
                response = requests.post(
                    f'{BASE_URL}/report/material_report',
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"❌ 报表查询失败: {response.status_code}")
                    break

                result = response.json()
                details = result.get('details', [])
                if not details:
                    break

                all_data.extend(details)

                if len(details) < page_size:
                    break
                page += 1

            except Exception as e:
                print(f"❌ 报表查询异常: {e}")
                break

        return all_data

    def get_video_details(self, photo_ids: List[str]) -> Dict[str, Dict]:
        """
        批量查询视频详情
        返回: {photo_id: {photo_name, url, cover_url, ...}}
        """
        video_map = {}
        unique_ids = list(set(pid for pid in photo_ids if pid))

        if not unique_ids:
            return {}

        print(f"📡 查询 {len(unique_ids)} 个视频详情...")

        for i in range(0, len(unique_ids), 100):
            batch = unique_ids[i:i + 100]
            payload = {
                'advertiser_id': self.advertiser_id,
                'photo_ids': batch
            }

            try:
                response = requests.post(
                    f'{BASE_URL}/file/ad/video/get',
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"❌ HTTP错误: {response.status_code}")
                    continue

                result = response.json()

                # 检查API返回码
                if result.get('code') != 0:
                    print(f"❌ API错误: {result.get('code')} - {result.get('message', result.get('msg'))}")
                    continue

                video_list = result.get('data', [])
                for v in video_list:
                    pid = v.get('photo_id')
                    if pid:
                        video_map[pid] = v

                print(f"  ✅ 本批返回 {len(video_list)} 条")

            except Exception as e:
                print(f"❌ 查询视频详情异常: {e}")
                continue

        return video_map

    def fetch_report_with_names(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取报表数据并合并视频名称
        返回: 报表数据 + photo_name, url, cover_url
        """
        # 1. 获取报表
        report_data = self.get_report(start_date, end_date)
        if not report_data:
            return []

        # 2. 提取 photo_id
        photo_ids = [item.get('photo_id') for item in report_data if item.get('photo_id')]

        # 3. 获取视频详情
        video_map = self.get_video_details(photo_ids)

        # 4. 合并数据
        result = []
        for item in report_data:
            photo_id = item.get('photo_id', '')
            video_info = video_map.get(photo_id, {})

            # 合并视频详情到报表数据
            merged = dict(item)
            merged['photo_name'] = video_info.get('photo_name', '')
            merged['url'] = video_info.get('url', '')           # 视频播放链接
            merged['cover_url'] = video_info.get('cover_url', '')  # 封面链接

            result.append(merged)

        return result