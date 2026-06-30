#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试快手接口返回字段 - 保存原始JSON"""

import requests
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KUAISHOU_ACCESS_TOKEN, KUAISHOU_ADVERTISER_ID


def test_api():
    url = 'https://ad.e.kuaishou.com/rest/openapi/v1/report/material_report'

    payload = {
        'advertiser_id': KUAISHOU_ADVERTISER_ID,
        'start_date': '2026-06-25',
        'end_date': '2026-06-25',
        'view_type': 5,
        'temporal_granularity': 'DAILY',
        'page': 1,
        'page_size': 100,
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

    headers = {
        'Access-Token': KUAISHOU_ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    print("=" * 70)
    print("📤 请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("-" * 70)

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    result = response.json()

    # 🔥 保存第一手原始JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"kuaishou_raw_response_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✅ 原始JSON已保存到: {filename}")
    print("-" * 70)

    print("📥 响应结果预览:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000] + "...")
    print("-" * 70)

    # 查找包含 "2026-06-17_010.mp4" 的数据
    details = result.get('details', [])
    print(f"\n📊 共返回 {len(details)} 条数据")

if __name__ == '__main__':
    test_api()