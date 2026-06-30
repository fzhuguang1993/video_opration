#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询快手数据，根据 trace_code 白名单分流到正常表或孤儿表"""

import requests
import json
import pymysql
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KUAISHOU_ACCESS_TOKEN, KUAISHOU_ADVERTISER_ID, DB_CFG

BASE_URL = 'https://ad.e.kuaishou.com/rest/openapi/v1'
HEADERS = {
    'Access-Token': KUAISHOU_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}


def fetch_report(start_date: str, end_date: str) -> list:
    """查询素材报表"""
    url = f'{BASE_URL}/report/material_report'
    all_data = []
    page = 1

    while True:
        payload = {
            'advertiser_id': KUAISHOU_ADVERTISER_ID,
            'start_date': start_date,
            'end_date': end_date,
            'view_type': 5,
            'temporal_granularity': 'DAILY',
            'page': page,
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

        print(f"📡 查询报表第 {page} 页...")
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            break

        result = response.json()
        details = result.get('details', [])
        if not details:
            break

        all_data.extend(details)
        print(f"  ✅ 本页 {len(details)} 条，累计 {len(all_data)} 条")

        if len(details) < 100:
            break
        page += 1

    return all_data


def fetch_video_details(photo_ids: list) -> dict:
    """查询视频详情，返回 photo_id -> info 字典"""
    url = f'{BASE_URL}/file/ad/video/get'
    name_map = {}

    unique_ids = list(set(pid for pid in photo_ids if pid))
    if not unique_ids:
        return {}

    print(f"\n📡 查询 {len(unique_ids)} 个视频详情...")

    for i in range(0, len(unique_ids), 100):
        batch = unique_ids[i:i + 100]
        payload = {
            'advertiser_id': KUAISHOU_ADVERTISER_ID,
            'photo_ids': batch
        }

        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            continue

        result = response.json()
        if result.get('code') != 0:
            print(f"❌ API错误: {result.get('code')} - {result.get('message', result.get('msg'))}")
            continue

        video_list = result.get('data', [])
        for v in video_list:
            pid = v.get('photo_id')
            if pid:
                name_map[pid] = v

        print(f"  ✅ 本批返回 {len(video_list)} 条")

    return name_map


def get_valid_trace_codes() -> set:
    """从 video_trace 表获取所有合法的 trace_code"""
    conn = pymysql.connect(**DB_CFG)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT DISTINCT trace_code FROM video_trace")
        rows = cursor.fetchall()
        return set([row[0] for row in rows])
    except Exception as e:
        print(f"⚠️ 查询 video_trace 失败: {e}")
        return set()
    finally:
        cursor.close()
        conn.close()


def extract_trace_code(photo_name: str) -> str:
    """从视频名称提取溯源码（前4位）"""
    if not photo_name:
        return ''
    return photo_name[:4] if len(photo_name) >= 4 else photo_name


def save_to_video_stat(item: dict, stat_date: str) -> bool:
    """保存到 video_stat 表（正常表）"""
    conn = pymysql.connect(**DB_CFG)
    cursor = conn.cursor()

    sql = """
        INSERT INTO video_stat (
            trace_code, total_cost, daily_cost, week_cost,
            cover_impression, material_impression, action_count,
            cover_click, cover_click_rate, impression_1k_cost,
            click_1k_cost, photo_click_cost, action_cost,
            action_rate, conversion_count, conversion_rate,
            three_sec_rate, five_sec_rate, seventy_five_rate,
            end_rate, photo_url, cover_url, stat_date
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            updated_at = NOW()
    """

    params = (
        item['trace_code'],
        item['total_cost'], item['daily_cost'], item['week_cost'],
        item['cover_impression'], item['material_impression'], item['action_count'],
        item['cover_click'], item['cover_click_rate'], item['impression_1k_cost'],
        item['click_1k_cost'], item['photo_click_cost'], item['action_cost'],
        item['action_rate'], item['conversion_count'], item['conversion_rate'],
        item['three_sec_rate'], item['five_sec_rate'], item['seventy_five_rate'],
        item['end_rate'], item['photo_url'], item['cover_url'], stat_date
    )

    try:
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ video_stat 插入失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def save_to_orphan(photo_id: str, photo_name: str, trace_code: str, stat_date: str) -> bool:
    """保存到 kuaishou_orphan_video 表（孤儿表）"""
    # photo_name 为空说明是脏数据，不写入
    if not photo_name or not photo_name.strip():
        print(f"⚠️ 跳过脏数据: photo_id={photo_id}, photo_name为空")
        return False

    conn = pymysql.connect(**DB_CFG)
    cursor = conn.cursor()

    # 先检查是否已存在
    cursor.execute(
        "SELECT id FROM kuaishou_orphan_video WHERE photo_id = %s",
        (photo_id,)
    )
    existing = cursor.fetchone()

    if existing:
        sql = """
            UPDATE kuaishou_orphan_video
            SET last_found_date = %s, updated_at = NOW()
            WHERE photo_id = %s
        """
        params = (stat_date, photo_id)
    else:
        sql = """
            INSERT INTO kuaishou_orphan_video (
                photo_id, photo_name, trace_code, last_found_date, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, 0, NOW(), NOW())
        """
        params = (photo_id, photo_name, trace_code, stat_date)

    try:
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 孤儿表插入失败: photo_id={photo_id}, error={e}")
        return False
    finally:
        cursor.close()
        conn.close()


def map_to_video_stat(report_item: dict, video_map: dict, stat_date: str) -> dict:
    """映射报表数据到 video_stat 字段"""
    photo_id = report_item.get('photo_id', '')
    video_info = video_map.get(photo_id, {})
    photo_name = video_info.get('photo_name', '')

    charge = report_item.get('charge', 0) or 0
    aclick = report_item.get('aclick', 0) or 0
    submit = report_item.get('submit', 0) or 0
    conversion_count = submit  # submit 就是 conversion_count

    return {
        'trace_code': extract_trace_code(photo_name),
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
        'conversion_count': conversion_count,
        'conversion_rate': conversion_count / aclick if aclick > 0 else 0,
        'three_sec_rate': report_item.get('play_3s_ratio', 0) or 0,
        'five_sec_rate': report_item.get('play_5s_ratio', 0) or 0,
        'seventy_five_rate': report_item.get('ad_photo_played_75percent_ratio', 0) or 0,
        'end_rate': report_item.get('play_end_ratio', 0) or 0,
        'photo_url': video_info.get('url', ''),  # 视频详情接口返回的是 url，不是 photo_url
        'cover_url': video_info.get('cover_url', ''),
        'photo_id': photo_id,
        'photo_name': photo_name,
        'stat_date': stat_date,
    }


def main():
    # 默认查询昨天
    yesterday = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    target_date = sys.argv[1] if len(sys.argv) > 1 else yesterday

    print("=" * 70)
    print(f"🎯 目标日期: {target_date}")
    print("=" * 70)

    # 1. 获取白名单
    print("\n【步骤1】获取合法 trace_code 白名单...")
    valid_trace_codes = get_valid_trace_codes()
    print(f"✅ 白名单共 {len(valid_trace_codes)} 个 trace_code")

    # 2. 查询报表
    print("\n【步骤2】查询报表数据...")
    report_data = fetch_report(target_date, target_date)

    if not report_data:
        print("❌ 报表无数据，退出")
        return

    print(f"✅ 报表共 {len(report_data)} 条")

    # 3. 提取 photo_id
    photo_ids = [item.get('photo_id') for item in report_data if item.get('photo_id')]
    print(f"\n📋 提取 {len(photo_ids)} 个 photo_id")

    # 4. 查询视频详情
    print("\n【步骤3】查询视频详情...")
    video_map = fetch_video_details(photo_ids)
    print(f"✅ 获取 {len(video_map)} 个视频详情")

    # 5. 映射 & 分流
    print("\n【步骤4】数据映射 & 分流...")
    stat_date = report_data[0].get('stat_date', target_date) if report_data else target_date

    normal_count = 0
    orphan_count = 0
    dirty_count = 0

    for item in report_data:
        photo_id = item.get('photo_id', '')
        video_info = video_map.get(photo_id, {})
        photo_name = video_info.get('photo_name', '')
        trace_code = extract_trace_code(photo_name)

        # 脏数据：photo_name 为空
        if not photo_name or not photo_name.strip():
            print(f"⚠️ 脏数据: photo_id={photo_id}, photo_name为空，跳过")
            dirty_count += 1
            continue

        if not trace_code:
            print(f"⚠️ photo_id={photo_id} 无 trace_code，进孤儿表")
            if save_to_orphan(photo_id, photo_name, trace_code, stat_date):
                orphan_count += 1
            continue

        if trace_code in valid_trace_codes:
            mapped = map_to_video_stat(item, video_map, stat_date)
            if save_to_video_stat(mapped, stat_date):
                normal_count += 1
        else:
            print(f"⚠️ trace_code={trace_code} 不在白名单，进孤儿表 (photo_id={photo_id})")
            if save_to_orphan(photo_id, photo_name, trace_code, stat_date):
                orphan_count += 1

    # 6. 汇总
    print("\n" + "=" * 70)
    print("📊 汇总:")
    print(f"  总数据: {len(report_data)} 条")
    print(f"  ✅ 正常表: {normal_count} 条")
    print(f"  ⚠️ 孤儿表: {orphan_count} 条")
    print(f"  🗑️ 脏数据(跳过): {dirty_count} 条")
    print("=" * 70)


if __name__ == '__main__':
    main()