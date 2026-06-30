# test_api_raw.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api.kuaishou_loader import KuaishouReportLoader
import json

loader = KuaishouReportLoader()
data = loader.fetch_report_with_names("2026-06-25", "2026-06-25")

if data:
    # 查看第一条数据的完整字段
    print(json.dumps(data[0], indent=2, ensure_ascii=False))
    print(f"\n总数据量: {len(data)}")
    total_charge = sum(item.get('charge', 0) for item in data)
    print(f"总消耗: {total_charge}")
else:
    print("无数据返回")