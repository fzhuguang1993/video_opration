#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目整理脚本 - 将待删除文件移到回收站
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class ProjectCleaner:
    """项目整理器"""

    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.recycle_bin = self.root / ".recycle_bin"
        self.moved_files = []
        self.not_found = []
        self.errors = []

        # 待移动的文件列表（相对于项目根目录）
        self.files_to_move = [
            # 旧入口文件
            "package.py",
            "movie_work_space.py",

            # 临时脚本
            "scan_structure.py",
            "migrate_db.py",

            # 测试文件
            "test/analyze_deps.py",
            "test/debug_style.py",

            # 空文件
            "auth/init.py",

            # 旧组件（已被替代）
            "ui/components/params_panel.py",

            # 旧表格行（已被合并）
            "widgets/video_table_row.py",

            # 占位页面（保留核心页面，占位可移走）
            "ui/pages/assets_page.py",
            "ui/pages/reports_page.py",
            "ui/pages/settings_page.py",
            "ui/pages/batch_paste_page.py",
            "ui/pages/toolbox_page.py",
        ]

        # 需要保留的核心页面（不移走）
        self.keep_pages = [
            "ui/pages/__init__.py",
            "ui/pages/dashboard_page.py",
            "ui/pages/watermark_page.py",
        ]

    def create_recycle_bin(self):
        """创建回收站"""
        if not self.recycle_bin.exists():
            self.recycle_bin.mkdir(parents=True)
            print(f"📁 创建回收站: {self.recycle_bin}")
        else:
            print(f"📁 回收站已存在: {self.recycle_bin}")

        # 创建回收站内的日期子目录
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recycle_date_dir = self.recycle_bin / date_str
        self.recycle_date_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 本次回收目录: {self.recycle_date_dir}")
        print("")

    def move_file(self, rel_path: str):
        """移动文件到回收站"""
        src = self.root / rel_path

        if not src.exists():
            self.not_found.append(rel_path)
            print(f"⚠️  文件不存在: {rel_path}")
            return

        # 检查是否在保留列表中
        if rel_path in self.keep_pages:
            print(f"🛡️  跳过（保留）: {rel_path}")
            return

        # 检查是否在回收站中已有同名文件
        dest = self.recycle_date_dir / src.name
        if dest.exists():
            # 加时间戳
            dest = self.recycle_date_dir / f"{src.stem}_{datetime.now().strftime('%H%M%S')}{src.suffix}"

        try:
            # 确保目标目录存在
            dest.parent.mkdir(parents=True, exist_ok=True)
            # 移动文件
            shutil.move(str(src), str(dest))
            self.moved_files.append((rel_path, str(dest.relative_to(self.root))))
            print(f"✅ 移动: {rel_path} → {dest.relative_to(self.root)}")
        except Exception as e:
            self.errors.append((rel_path, str(e)))
            print(f"❌ 移动失败: {rel_path} - {e}")

    def dry_run(self):
        """预览要移动的文件"""
        print("=" * 70)
        print("🔍 预览要移动的文件")
        print("=" * 70)
        print("")

        print("📋 将移动到回收站的文件:")
        for f in self.files_to_move:
            src = self.root / f
            status = "✅" if src.exists() else "❌"
            print(f"  {status} {f}")

        print("")
        print("🛡️ 保留的文件（不移走）:")
        for f in self.keep_pages:
            print(f"  📌 {f}")

        print("")
        print(f"📁 回收站路径: {self.recycle_bin}")
        print("")
        print("=" * 70)

    def run(self, confirm: bool = True):
        """执行整理"""
        print("=" * 70)
        print("🧹 项目整理 - 文件移动到回收站")
        print("=" * 70)
        print(f"项目路径: {self.root}")
        print(f"回收站: {self.recycle_bin}")
        print("=" * 70)
        print("")

        # 预览
        self.dry_run()

        if confirm:
            response = input("确认执行移动操作？ (y/n): ").strip().lower()
            if response != 'y':
                print("❌ 操作已取消")
                return False

        # 创建回收站
        self.create_recycle_bin()

        # 移动文件
        print("📦 开始移动文件...")
        print("")

        for f in self.files_to_move:
            self.move_file(f)

        # 打印总结
        print("")
        print("=" * 70)
        print("📊 整理结果")
        print("=" * 70)
        print(f"✅ 成功移动: {len(self.moved_files)} 个文件")
        print(f"⚠️  文件不存在: {len(self.not_found)} 个")
        print(f"❌ 移动失败: {len(self.errors)} 个")

        if self.moved_files:
            print("\n📋 已移动的文件:")
            for src, dest in self.moved_files:
                print(f"  {src} → {dest}")

        if self.not_found:
            print("\n⚠️ 不存在的文件:")
            for f in self.not_found:
                print(f"  {f}")

        if self.errors:
            print("\n❌ 移动失败:")
            for f, err in self.errors:
                print(f"  {f}: {err}")

        print("")
        print("💡 如需恢复，请查看回收站:")
        print(f"  cd {self.recycle_date_dir}")
        print("=" * 70)

        return len(self.errors) == 0

    def restore_all(self):
        """从回收站恢复所有文件"""
        if not self.recycle_bin.exists():
            print("❌ 回收站不存在")
            return

        print("=" * 70)
        print("♻️ 从回收站恢复文件")
        print("=" * 70)

        restored = 0
        for item in self.recycle_bin.rglob('*'):
            if item.is_file():
                dest = self.root / item.name
                # 检查是否有同名文件
                if dest.exists():
                    print(f"⚠️  目标文件已存在，跳过: {item.name}")
                    continue
                shutil.move(str(item), str(dest))
                print(f"✅ 恢复: {item.name}")
                restored += 1

        print("")
        print(f"✅ 恢复了 {restored} 个文件")


def main():
    """主函数"""
    project_path = "/Users/leiliang/PycharmProjects/movie_opration"

    if not os.path.exists(project_path):
        print(f"❌ 路径不存在: {project_path}")
        sys.exit(1)

    cleaner = ProjectCleaner(project_path)

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            cleaner.dry_run()
            return
        elif sys.argv[1] == "--restore":
            cleaner.restore_all()
            return

    # 执行整理
    cleaner.run(confirm=True)


if __name__ == "__main__":
    main()