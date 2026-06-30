#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试：查看 TreeBuilder 内部的数据结构"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from ui.pages.assets.page import AssetsPage
from ui.pages.assets.tree_builder import TreeBuilder


def main():
    app = QApplication(sys.argv)

    # 创建 AssetsPage 实例
    page = AssetsPage()

    # 模拟用户登录
    user_info = {
        'user_id': 1,
        'role': 1,
        'real_name': '嬴政'
    }
    page.set_current_user(user_info)

    def print_data():
        print("=" * 70)
        print("📊 TreeBuilder 内部数据检查")
        print("=" * 70)

        # 获取当前 builder
        builder = page._current_builder
        if not builder:
            print("❌ builder 为 None")
            app.quit()
            return

        print(f"\n📋 builder 类型: {type(builder)}")
        print(f"📋 builder.stat_map 长度: {len(builder.stat_map)}")

        if builder.stat_map:
            print("\n📋 stat_map 中的样例数据 (前3条):")
            for i, (key, value) in enumerate(list(builder.stat_map.items())[:3]):
                print(f"   [{i}] {key}: {value}")

        print(f"\n📋 builder._displayed_data 长度: {len(builder._displayed_data)}")

        if builder._displayed_data:
            print("\n📋 _displayed_data 第一条数据的所有 keys:")
            print(f"   {list(builder._displayed_data[0].keys())}")

            print("\n📋 _displayed_data 第一条数据完整内容:")
            for key, value in builder._displayed_data[0].items():
                if isinstance(value, list):
                    print(f"   {key}: {value} (长度: {len(value)})")
                elif isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")

        print("\n" + "=" * 70)

        # 打印 builder._format_row 处理后的数据
        if builder._displayed_data:
            print("\n📊 _format_row 处理后的数据 (前3条):")
            for i, record in enumerate(builder._displayed_data[:3]):
                trace_code = record.get('trace_code', 'N/A')
                values, photo_url, cover_url = builder._format_row(trace_code, record, i+1)
                print(f"\n   [{i}] trace_code: {trace_code}")
                print(f"       values 长度: {len(values)}")
                print(f"       photo_url: {photo_url}")
                print(f"       cover_url: {cover_url}")
                # 显示统计字段
                stat = builder._get_stat(trace_code)
                if stat:
                    print(f"       stat 中的 total_cost: {stat.get('total_cost', 'N/A')}")
                    print(f"       stat 中的 photo_url: {stat.get('photo_url', 'N/A')}")
                else:
                    print(f"       ❌ 没有统计数据")

        print("=" * 70)
        app.quit()

    # 使用 QTimer 延迟执行，等待数据加载
    from PySide6.QtCore import QTimer
    QTimer.singleShot(1000, print_data)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()