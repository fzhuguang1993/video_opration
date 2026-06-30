#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库同步脚本 - 从测试库导出表结构和数据，导入到生产库"""

import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CFG

# 测试库配置（源库）
SOURCE_DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "yunying_test",
    "charset": "utf8mb4",
}

# 生产库配置（目标库）
TARGET_DB = {
    "host": "rm-cn-5yd3eq34z000d37o.rwlb.rds.aliyuncs.com",
    "port": 3306,
    "user": "yunying",
    "password": "JvX0Z&kHHNk#6^0b(Up%",
    "database": "yunying_center",
    "charset": "utf8mb4",
}


def get_connection(db_config):
    """获取数据库连接"""
    return pymysql.connect(**db_config)


def get_table_list(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_create_table_sql(conn, table_name):
    """获取建表语句"""
    cursor = conn.cursor()
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    result = cursor.fetchone()
    cursor.close()
    return result[1]


def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table_name}`")
    data = cursor.fetchall()
    cursor.close()
    return data


def get_table_columns(conn, table_name):
    """获取表列名"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns


def drop_all_tables(conn):
    """删除所有表（外键约束处理）"""
    cursor = conn.cursor()

    # 先禁用外键检查
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 获取所有表
    tables = get_table_list(conn)
    print(f"  📋 找到 {len(tables)} 个表")

    # 删除所有表
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            print(f"  ✅ 删除表: {table}")
        except Exception as e:
            print(f"  ❌ 删除表 {table} 失败: {e}")

    # 启用外键检查
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    print(f"  ✅ 所有表已删除")


def create_table(conn, table_name, create_sql):
    """创建表"""
    cursor = conn.cursor()
    try:
        cursor.execute(create_sql)
        print(f"  ✅ 创建表: {table_name}")
    except Exception as e:
        print(f"  ❌ 创建表 {table_name} 失败: {e}")
        raise
    finally:
        cursor.close()


def insert_data(conn, table_name, columns, data):
    """插入数据"""
    if not data:
        print(f"  ⏭️ 表 {table_name} 无数据，跳过")
        return

    cursor = conn.cursor()
    placeholders = ",".join(["%s"] * len(columns))
    column_names = ",".join([f"`{col}`" for col in columns])
    sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"

    try:
        cursor.executemany(sql, data)
        conn.commit()
        print(f"  ✅ 插入 {len(data)} 条数据到: {table_name}")
    except Exception as e:
        conn.rollback()
        print(f"  ❌ 插入数据到 {table_name} 失败: {e}")
        raise
    finally:
        cursor.close()


def sync_database():
    """同步数据库"""
    print("=" * 70)
    print("📊 数据库同步脚本")
    print("=" * 70)
    print(f"\n📌 源库: {SOURCE_DB['host']}/{SOURCE_DB['database']}")
    print(f"📌 目标库: {TARGET_DB['host']}/{TARGET_DB['database']}")
    print("\n⚠️ 警告: 目标库的所有表将被删除并重新导入！")
    print("-" * 70)

    # 确认操作
    confirm = input("确认继续? (输入 yes 继续): ")
    if confirm.lower() != "yes":
        print("❌ 已取消")
        return

    print("\n开始同步...")
    print("-" * 70)

    source_conn = None
    target_conn = None

    try:
        # 连接数据库
        print("\n🔗 连接数据库...")
        source_conn = get_connection(SOURCE_DB)
        target_conn = get_connection(TARGET_DB)
        print("  ✅ 连接成功")

        # 获取源库所有表
        print("\n📋 获取源库表列表...")
        tables = get_table_list(source_conn)
        print(f"  ✅ 找到 {len(tables)} 个表: {', '.join(tables)}")

        # 删除目标库所有表
        print("\n🗑️ 删除目标库所有表...")
        drop_all_tables(target_conn)

        # 逐个同步表
        print("\n📥 同步表结构和数据...")
        for idx, table_name in enumerate(tables):
            print(f"\n  [{idx + 1}/{len(tables)}] 同步表: {table_name}")

            # 获取建表语句
            create_sql = get_create_table_sql(source_conn, table_name)

            # 创建表
            create_table(target_conn, table_name, create_sql)

            # 获取数据
            columns = get_table_columns(source_conn, table_name)
            data = get_table_data(source_conn, table_name)

            # 插入数据
            insert_data(target_conn, table_name, columns, data)

        print("\n" + "-" * 70)
        print("✅ 同步完成!")
        print(f"📊 共同步 {len(tables)} 个表")

    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()


if __name__ == "__main__":
    sync_database()