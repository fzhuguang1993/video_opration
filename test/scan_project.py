#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看完整项目结构"""

import os

PROJECT_ROOT = "/Users/leiliang/PycharmProjects/movie_opration"


def show_tree(path, prefix="", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = [".venv", "__pycache__", ".git", "node_modules", ".idea", ".pytest_cache"]

    # 获取当前目录内容
    items = []
    try:
        for item in os.listdir(path):
            if item in ignore_dirs:
                continue
            if item.startswith(".") and item not in [".DS_Store"]:
                continue
            items.append(item)
    except PermissionError:
        return

    # 排序：目录在前，文件在后
    dirs = sorted([i for i in items if os.path.isdir(os.path.join(path, i))])
    files = sorted([i for i in items if os.path.isfile(os.path.join(path, i))])
    items = dirs + files

    for i, item in enumerate(items):
        item_path = os.path.join(path, item)
        is_last = (i == len(items) - 1)

        # 连接符
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{item}")

        # 如果是目录，递归
        if os.path.isdir(item_path):
            extension = "    " if is_last else "│   "
            show_tree(item_path, prefix + extension, ignore_dirs)


if __name__ == "__main__":
    print("=" * 70)
    print(f"📂 项目结构: {PROJECT_ROOT}")
    print("=" * 70)
    print("")

    # 只显示核心目录，避免输出太多
    core_dirs = ["config", "core", "models", "services", "ui", "utils", "worker", "widgets"]

    print(f"{PROJECT_ROOT}/")
    for d in core_dirs:
        dir_path = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(dir_path):
            print(f"├── {d}/")
            show_tree(dir_path, "│   ")
    print("└── ...")