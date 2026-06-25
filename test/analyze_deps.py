#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目依赖分析脚本 v2 - 更准确地检测未被引用的文件
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ProjectAnalyzer:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.py_files = []
        self.file_imports = defaultdict(set)
        self.file_imported_by = defaultdict(set)
        self.all_references = set()

    def scan(self):
        print("📂 扫描Python文件...")
        for py_file in self.root.rglob('*.py'):
            if any(excl in py_file.parts for excl in ['.venv', 'venv', 'env', '.env']):
                continue
            if '__pycache__' in py_file.parts:
                continue
            self.py_files.append(py_file)
        print(f"  找到 {len(self.py_files)} 个Python文件")

    def analyze_imports(self):
        print("🔍 分析导入关系...")

        for py_file in self.py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                continue

            rel_path = str(py_file.relative_to(self.root))

            # 导入语句模式
            imported = set()
            lines = content.split('\n')

            for line in lines:
                line = line.strip()
                # import xxx
                if line.startswith('import '):
                    parts = line.replace('import ', '').split(',')
                    for p in parts:
                        mod = p.strip().split(' ')[0]
                        imported.add(mod)
                # from xxx import
                elif line.startswith('from '):
                    match = re.match(r'from\s+([\w.]+)\s+import', line)
                    if match:
                        mod = match.group(1)
                        imported.add(mod)

            self.file_imports[rel_path] = imported
            for mod in imported:
                self.all_references.add(mod)

                # 尝试匹配文件
                for target_file in self.py_files:
                    target_rel = str(target_file.relative_to(self.root))
                    # 匹配模块名
                    target_mod = target_rel.replace('.py', '').replace('/', '.')
                    if target_mod == mod or target_mod.endswith('.' + mod) or mod.endswith('.' + target_mod):
                        self.file_imported_by[target_rel].add(rel_path)
                        break

    def find_unused_files(self):
        print("🔎 查找未被引用的文件...")

        used_files = set()

        # 入口文件列表（手动补充）
        entry_files = [
            'main.py',
            'config.py',
            'ui/main_window.py',
            'ui/components/sidebar.py',
            'ui/components/top_bar.py',
        ]

        def collect_deps(rel_path):
            if rel_path in used_files:
                return
            used_files.add(rel_path)
            for imported in self.file_imports.get(rel_path, []):
                for target_file in self.py_files:
                    target_rel = str(target_file.relative_to(self.root))
                    target_mod = target_rel.replace('.py', '').replace('/', '.')
                    if target_mod == imported or target_mod.endswith('.' + imported):
                        if target_rel not in used_files:
                            collect_deps(target_rel)

        for entry in entry_files:
            if entry in [str(f.relative_to(self.root)) for f in self.py_files]:
                collect_deps(entry)

        all_files = {str(f.relative_to(self.root)) for f in self.py_files}
        unused = all_files - used_files

        return unused

    def generate_report(self):
        unused = self.find_unused_files()

        report = []
        report.append("=" * 70)
        report.append("🗑️ 建议删除的文件清单")
        report.append("=" * 70)
        report.append(f"总文件: {len(self.py_files)}")
        report.append(f"已使用: {len(self.py_files) - len(unused)}")
        report.append(f"未使用: {len(unused)}")
        report.append("=" * 70 + "\n")

        # 按是否可安全删除分组
        safe_to_delete = []
        caution = []

        for f in sorted(unused):
            imported_by = self.file_imported_by.get(f, set())
            if imported_by:
                caution.append((f, imported_by))
            else:
                safe_to_delete.append(f)

        report.append("✅ 可直接删除（完全未被引用）:")
        for f in safe_to_delete:
            report.append(f"  🗑️  {f}")

        if caution:
            report.append("\n⚠️ 需要确认（被其他文件引用，但入口未触发）:")
            for f, imported_by in caution:
                report.append(
                    f"  ⚠️  {f} (被 {', '.join(list(imported_by)[:3])}{' 等' if len(imported_by) > 3 else ''} 引用)")

        # 写入文件
        output_file = "cleanup_list.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"\n✅ 清理清单已生成: {output_file}")
        print(f"🗑️ 可直接删除: {len(safe_to_delete)} 个")
        print(f"⚠️ 需要确认: {len(caution)} 个")

        return safe_to_delete, caution


def main():
    project_path = "/Users/leiliang/PycharmProjects/movie_opration"

    if not os.path.exists(project_path):
        print(f"❌ 路径不存在: {project_path}")
        sys.exit(1)

    analyzer = ProjectAnalyzer(project_path)
    analyzer.scan()
    analyzer.analyze_imports()
    analyzer.generate_report()


if __name__ == "__main__":
    main()