#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小化快手数据获取脚本 - 只拿数据，不写库"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api.kuaishou_loader import KuaishouReportLoader


def main():
    print("=" * 60)
    print("📊 最小化快手数据获取")
    print("=" * 60)

    # 查询日期
    target_date = '2026-06-25'
    print(f"📅 查询日期: {target_date}")
    print("-" * 60)

    # 1. 初始化 Loader
    loader = KuaishouReportLoader()

    # 2. 获取数据
    data = loader.fetch_report_with_names(target_date, target_date)

    if not data:
        print("❌ 无数据")
        return

    print(f"✅ 获取到 {len(data)} 条数据")
    print("-" * 60)

    # 3. 打印前3条
    print("📋 前3条数据:")
    for i, item in enumerate(data[:3]):
        print(f"\n[{i + 1}] photo_id: {item.get('photo_id')}")
        print(f"    photo_name: {item.get('photo_name')}")
        print(f"    stat_date: {item.get('stat_date')}")
        print(f"    charge: {item.get('charge')}")
        print(f"    show: {item.get('show')}")
        print(f"    aclick: {item.get('aclick')}")
        print(f"    bclick: {item.get('bclick')}")

    # 4. 保存到文件
    output_file = f"kuaishou_data_{target_date}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("-" * 60)
    print(f"✅ 完整数据已保存到: {output_file}")


if __name__ == '__main__':
    main()