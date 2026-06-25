#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 从生产环境同步表结构和数据到本地测试库
"""

import pymysql
import sys

# ================================================================
# 生产环境配置
# ================================================================
PROD_CONFIG = {
    "host": "rm-cn-5yd3eq34z000d37o.rwlb.rds.aliyuncs.com",
    "port": 3306,
    "user": "yunying",
    "password": "JvX0Z&kHHNk#6^0b(Up%",
    "database": "yunying_center",
    "charset": "utf8mb4"
}

# ================================================================
# 本地测试环境配置
# ================================================================
TEST_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "yunying_test",
    "charset": "utf8mb4"
}

# 需要迁移的表
TABLES = [
    "sys_user",
    "video_trace",
    "trace_code_pool",
    "video_bind"
]


def get_connection(config):
    """获取数据库连接"""
    return pymysql.connect(**config)


def get_table_structure(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    result = cursor.fetchone()
    cursor.close()
    return result[1] if result else None


def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table_name}`")
    result = cursor.fetchall()
    cursor.close()
    return result


def get_table_columns(conn, table_name):
    """获取表的列名"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`")
    result = cursor.fetchall()
    cursor.close()
    return [col[0] for col in result]


def main():
    """主函数"""
    print("=" * 60)
    print("📦 数据库迁移工具")
    print("=" * 60)
    print(f"源数据库: {PROD_CONFIG['host']}/{PROD_CONFIG['database']}")
    print(f"目标数据库: {TEST_CONFIG['host']}/{TEST_CONFIG['database']}")
    print("=" * 60)

    prod_conn = None
    test_conn = None

    try:
        # 连接数据库
        print("🔗 连接数据库...")
        prod_conn = get_connection(PROD_CONFIG)
        test_conn = get_connection(TEST_CONFIG)
        print("✅ 数据库连接成功")

        # 切换本地测试库
        test_cursor = test_conn.cursor()
        test_cursor.execute(f"USE `{TEST_CONFIG['database']}`")

        for table_name in TABLES:
            print(f"\n📋 处理表: {table_name}")

            # 1. 获取表结构
            print(f"  📄 获取表结构...")
            create_sql = get_table_structure(prod_conn, table_name)
            if not create_sql:
                print(f"  ⚠️ 表 {table_name} 不存在于生产库，跳过")
                continue

            # 2. 删除本地旧表（如果存在）
            test_cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            print(f"  🗑️ 删除旧表（如果存在）")

            # 3. 创建新表
            test_cursor.execute(create_sql)
            print(f"  ✅ 创建表成功")

            # 4. 获取数据
            print(f"  📊 获取数据...")
            columns = get_table_columns(prod_conn, table_name)
            data = get_table_data(prod_conn, table_name)

            if data:
                # 5. 插入数据
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"

                print(f"  📝 插入 {len(data)} 条数据...")
                for row in data:
                    test_cursor.execute(insert_sql, row)
                test_conn.commit()
                print(f"  ✅ 插入完成")

                # 重置自增ID
                if table_name == "sys_user":
                    max_id = max([row[0] for row in data]) if data else 0
                    test_cursor.execute(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = {max_id + 1}")
            else:
                print(f"  ℹ️ 表 {table_name} 没有数据")

        print("\n" + "=" * 60)
        print("🎉 迁移完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if prod_conn:
            prod_conn.close()
        if test_conn:
            test_conn.close()


if __name__ == "__main__":
    main()