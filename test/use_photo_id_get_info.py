#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据photo_id查询单个视频详细信息"""

import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KUAISHOU_ACCESS_TOKEN, KUAISHOU_ADVERTISER_ID


def fetch_video_info(photo_id):
    """根据photo_id查询视频详细信息"""
    url = 'https://ad.e.kuaishou.com/rest/openapi/v1/file/ad/video/list'

    payload = {
        'advertiser_id': KUAISHOU_ADVERTISER_ID,
        'photo_ids': [photo_id]
    }

    headers = {
        'Access-Token': KUAISHOU_ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    print("=" * 60)
    print(f"📤 查询视频ID: {photo_id}")
    print("=" * 60)
    print("📤 请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("-" * 60)

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    result = response.json()

    print("📥 响应结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get('code') != 0:
        print(f"❌ API错误: {result.get('code')} - {result.get('msg')}")
        return None

    return result


def main():
    # 默认查询你给的ID
    photo_id = sys.argv[1] if len(sys.argv) > 1 else '5226709043025404383'

    result = fetch_video_info(photo_id)

    if result and result.get('code') == 0:
        data = result.get('data', [])
        if data:
            print("\n" + "=" * 60)
            print("✅ 视频信息:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ 未找到该视频")


if __name__ == '__main__':
    main()