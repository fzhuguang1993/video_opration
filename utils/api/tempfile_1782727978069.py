# test/test_sync_data.py
"""测试同步数据 - 查看API返回 & 写入情况"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from datetime import datetime, timedelta
from config import DB_CFG
from utils.api.kuaishou_loader import KuaishouReportLoader


def check_api_data(target_date: str):
    """查看 API 返回的数据情况"""
    print(f"\n{'='*60}")
    print(f"📡 查询 API 数据: {target_date}")
    print(f"{'='*60}")

    loader = KuaishouReportLoader()
    data = loader.fetch_report_with_names(target_date, target_date)

    if not data:
        print("❌ API 无数据返回")
        return

    print(f"✅ API 返回 {len(data)} 条数据\n")

    valid = 0
    invalid = 0
    for item in data:
        photo_name = item.get('photo_name', '')
        photo_id = item.get('photo_id', '')
        charge = item.get('charge', 0)
        trace_code = photo_name[:4] if len(photo_name) >= 4 else ''

        if photo_name and len(photo_name) >= 4:
            valid += 1
            status = "✅"
        else:
            invalid += 1
            status = "❌"

        print(f"  {status} photo_id={photo_id}  name={photo_name[:40]:40s}  "
              f"trace={trace_code or '-':4s}  charge={charge}")

    print(f"\n📊 统计: 总计 {len(data)} | 有效 {valid} | 无效 {invalid}")


def check_db_data():
    """查看数据库中 video_stat 的数据"""
    print(f"\n{'='*60}")
    print(f"📦 数据库 video_stat 数据")
    print(f"{'='*60}")

    conn = pymysql.connect(**DB_CFG)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM video_stat")
    total = cur.fetchone()[0]
    print(f"总记录数: {total}\n")

    if total == 0:
        print("⚠️ video_stat 表为空")
    else:
        cur.execute("""
            SELECT trace_code, total_cost, daily_cost, week_cost,
                   cover_impression, material_impression, action_count,
                   three_sec_rate, five_sec_rate, end_rate,
                   photo_url IS NOT NULL AND photo_url != '' AS has_photo_url,
                   cover_url IS NOT NULL AND cover_url != '' AS has_cover_url,
                   stat_date
            FROM video_stat
            ORDER BY total_cost DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        print(f"{'溯源码':6s} {'花费':>8s} {'日花费':>8s} {'周花费':>8s} "
              f"{'封面曝光':>8s} {'素材曝光':>8s} {'行为数':>6s} "
              f"{'3s':>6s} {'5s':>6s} {'完播':>6s} {'视频链接':>6s} {'封面链接':>6s} {'日期':>10s}")
        print("-" * 120)
        for row in rows:
            print(f"{row[0]:6s} {row[1]:8.2f} {row[2]:8.2f} {row[3]:8.2f} "
                  f"{row[4]:8d} {row[5]:8d} {row[6]:6d} "
                  f"{row[7]:6.2f} {row[8]:6.2f} {row[9]:6.2f} "
                  f"{'✅' if row[10] else '❌':>6s} {'✅' if row[11] else '❌':>6s} "
                  f"{str(row[12]):>10s}")

    cur.close()
    conn.close()


def check_orphan_data():
    """查看孤儿表数据"""
    print(f"\n{'='*60}")
    print(f"📦 孤儿表 kuaishou_orphan_video")
    print(f"{'='*60}")

    conn = pymysql.connect(**DB_CFG)
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM kuaishou_orphan_video")
        total = cur.fetchone()[0]
        print(f"总记录数: {total}\n")

        if total > 0:
            cur.execute("SELECT photo_id, photo_name, last_found_date FROM kuaishou_orphan_video ORDER BY last_found_date DESC LIMIT 10")
            for row in cur.fetchall():
                print(f"  photo_id={row[0]}  name={row[1]}  date={row[2]}")
    except Exception as e:
        print(f"⚠️ 查询孤儿表失败: {e}")

    cur.close()
    conn.close()


def sync_and_check(target_date: str):
    """执行同步并检查结果"""
    print(f"\n{'='*60}")
    print(f"🔄 执行同步: {target_date}")
    print(f"{'='*60}")

    from services.kuaishou_sync import sync_kuaishou_data
    result = sync_kuaishou_data(start_date=target_date, end_date=target_date)

    print(f"\n📊 同步结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    target_date = "2026-06-25"

    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    print(f"🎯 目标日期: {target_date}")

    check_api_data(target_date)
    check_db_data()
    check_orphan_data()

    answer = input(f"\n是否同步 {target_date} 的数据? (y/n): ").strip().lower()
    if answer == 'y':
        sync_and_check(target_date)
        check_db_data()
