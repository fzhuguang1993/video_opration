#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试数据库连接"""

import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CFG


def test_connection():
    print("=" * 50)
    print("🔌 测试数据库连接")
    print("=" * 50)

    print(f"📌 配置信息:")
    print(f"   Host: {DB_CFG.get('host')}")
    print(f"   Port: {DB_CFG.get('port')}")
    print(f"   User: {DB_CFG.get('user')}")
    print(f"   Password: {'*' * len(DB_CFG.get('password', ''))}")
    print(f"   Database: {DB_CFG.get('database')}")
    print("-" * 50)

    try:
        conn = pymysql.connect(**DB_CFG)
        print("✅ 连接成功！")

        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print(f"✅ 查询测试: {result}")

        cur.close()
        conn.close()
        print("✅ 连接已关闭")
        print("=" * 50)
        return True

    except pymysql.err.OperationalError as e:
        print(f"❌ 连接失败: {e}")
        if e.args[0] == 1045:
            print("   💡 密码错误，请检查 config.py 中的 password")
        elif e.args[0] == 2003:
            print("   💡 无法连接到 MySQL 服务，请确认 MySQL 是否启动")
        elif e.args[0] == 1049:
            print("   💡 数据库不存在，请确认数据库名称")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_connection()