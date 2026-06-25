#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构扫描脚本 - 扫描并生成项目目录树和文件列表
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json


def scan_project(root_path: str, output_file: str = "project_structure.txt"):
    """扫描项目结构"""

    root = Path(root_path).resolve()

    # 要排除的目录
    exclude_dirs = {
        '.venv', 'venv', 'env', '.env',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.git', '.svn', '.hg',
        'node_modules', 'dist', 'build',
        'logs', 'temp', 'tmp',
        'site-packages', 'dist-packages',
        '.idea', '.vscode', '.DS_Store'
    }

    # 要排除的文件扩展名
    exclude_extensions = {
        '.pyc', '.pyo', '.pyd',
        '.so', '.dylib', '.dll',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.mp4', '.avi', '.mov', '.mkv',
        '.qm', '.ts', '.qml', '.sip'
    }

    result = {
        "project_root": str(root),
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": [],
        "directories": [],
        "statistics": {
            "total_files": 0,
            "total_dirs": 0,
            "python_files": 0,
            "other_files": 0
        }
    }

    # 收集所有文件和目录
    for item in root.rglob('*'):
        # 跳过排除的目录
        if any(excl in item.parts for excl in exclude_dirs):
            continue

        rel_path = item.relative_to(root)

        if item.is_dir():
            result["directories"].append(str(rel_path))
            result["statistics"]["total_dirs"] += 1
        else:
            # 跳过排除的文件类型
            if item.suffix in exclude_extensions:
                continue
            if item.name.startswith('.'):
                continue

            result["files"].append(str(rel_path))
            result["statistics"]["total_files"] += 1

            if item.suffix == '.py':
                result["statistics"]["python_files"] += 1
            else:
                result["statistics"]["other_files"] += 1

    # 排序
    result["directories"].sort()
    result["files"].sort()

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write(f"项目结构扫描报告\n")
        f.write(f"项目路径: {result['project_root']}\n")
        f.write(f"扫描时间: {result['scan_time']}\n")
        f.write("=" * 70 + "\n\n")

        f.write("📊 统计信息:\n")
        f.write(f"  - 总目录数: {result['statistics']['total_dirs']}\n")
        f.write(f"  - 总文件数: {result['statistics']['total_files']}\n")
        f.write(f"  - Python文件: {result['statistics']['python_files']}\n")
        f.write(f"  - 其他文件: {result['statistics']['other_files']}\n")
        f.write("\n" + "=" * 70 + "\n\n")

        f.write("📁 目录结构:\n")
        for d in result["directories"]:
            f.write(f"  📁 {d}/\n")
        f.write("\n" + "=" * 70 + "\n\n")

        f.write("📄 文件列表:\n")
        for fname in result["files"]:
            # 标记 Python 文件
            if fname.endswith('.py'):
                f.write(f"  🐍 {fname}\n")
            else:
                f.write(f"  📄 {fname}\n")

    print(f"✅ 扫描完成，结果保存到: {output_file}")
    print(f"📊 统计: {result['statistics']['total_files']} 个文件, {result['statistics']['total_dirs']} 个目录")
    print(f"🐍 Python文件: {result['statistics']['python_files']} 个")

    return result


def main():
    # 项目根目录
    project_path = "/Users/leiliang/PycharmProjects/movie_opration"

    if not os.path.exists(project_path):
        print(f"❌ 路径不存在: {project_path}")
        sys.exit(1)

    scan_project(project_path, "project_structure.txt")

    # 生成JSON格式（便于程序读取）
    result = scan_project(project_path, "project_structure.json")


if __name__ == "__main__":
    main()