#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目自检脚本 - 验证所有核心功能是否正常
"""

import sys
import os
import importlib
import traceback
from pathlib import Path


class SelfChecker:
    """自检器"""

    def __init__(self):
        self.root = Path(__file__).parent
        self.results = []
        self.passed = 0
        self.failed = 0
        self.errors = []

    def log(self, msg: str, level: str = "info"):
        """日志输出"""
        icons = {
            "info": "📌",
            "pass": "✅",
            "fail": "❌",
            "warning": "⚠️",
            "title": "="
        }
        print(f"{icons.get(level, '📌')} {msg}")

    def check_import(self, module_name: str, display_name: str = None):
        """检查模块导入"""
        if display_name is None:
            display_name = module_name

        try:
            importlib.import_module(module_name)
            self.passed += 1
            self.log(f"导入 {display_name} ... 成功", "pass")
            return True
        except Exception as e:
            self.failed += 1
            self.errors.append(f"导入 {display_name} 失败: {str(e)}")
            self.log(f"导入 {display_name} ... 失败: {str(e)}", "fail")
            return False

    def check_imports(self):
        """检查所有核心模块"""
        self.log("", "title")
        self.log("📦 检查模块导入", "title")
        self.log("", "title")

        modules = [
            # 核心模块
            ("core.config", "core.config"),
            ("core.logger", "core.logger"),
            ("core.database", "core.database"),
            ("core.video_service", "core.video_service"),

            # UI 组件
            ("ui.main_window", "ui.main_window"),
            ("ui.components.sidebar", "ui.components.sidebar"),
            ("ui.components.top_bar", "ui.components.top_bar"),
            ("ui.components.collapsible_params_panel", "ui.components.collapsible_params_panel"),
            ("ui.components.tool_panel", "ui.components.tool_panel"),

            # 页面
            ("ui.pages", "ui.pages"),

            # 小部件
            ("widgets.video_table", "widgets.video_table"),
            ("widgets.clickable_label", "widgets.clickable_label"),
            ("widgets.param_hint_btn", "widgets.param_hint_btn"),
            ("widgets.thumbnail_label", "widgets.thumbnail_label"),
            ("widgets.tool_select_dialog", "widgets.tool_select_dialog"),
            ("widgets.trace_dialog", "widgets.trace_dialog"),

            # 工具
            ("utils.ffmpeg_utils", "utils.ffmpeg_utils"),
            ("utils.file_utils", "utils.file_utils"),
            ("utils.smb_utils", "utils.smb_utils"),
            ("utils.trace_utils", "utils.trace_utils"),
            ("utils.tools", "utils.tools"),
            ("utils.tools.base_tool", "utils.tools.base_tool"),
            ("utils.tools.batch_input_tool", "utils.tools.batch_input_tool"),

            # 工作线程
            ("worker.watermark_worker", "worker.watermark_worker"),

            # 认证
            ("auth.login_dialog", "auth.login_dialog"),
            ("auth.change_pwd_dialog", "auth.change_pwd_dialog"),
        ]

        # 尝试导入所有模块
        for module, display in modules:
            self.check_import(module, display)

    def check_config(self):
        """检查配置"""
        self.log("", "title")
        self.log("⚙️ 检查配置", "title")
        self.log("", "title")

        try:
            from core.config import get_config
            config = get_config()
            self.log(f"应用名称: {config.APP_NAME}", "info")
            self.log(f"应用版本: {config.APP_VERSION}", "info")
            self.log(f"窗口大小: {config.WINDOW_MIN_WIDTH}x{config.WINDOW_MIN_HEIGHT}", "info")
            self.passed += 1
        except Exception as e:
            self.failed += 1
            self.errors.append(f"配置加载失败: {str(e)}")
            self.log(f"配置加载失败: {str(e)}", "fail")

        # 检查数据库配置
        try:
            import config as root_config
            env = getattr(root_config, 'ENV', 'unknown')
            db_cfg = getattr(root_config, 'DB_CFG', {})
            self.log(f"当前环境: {env}", "info")
            self.log(f"数据库: {db_cfg.get('host', 'unknown')}/{db_cfg.get('database', 'unknown')}", "info")
            self.passed += 1
        except Exception as e:
            self.failed += 1
            self.errors.append(f"数据库配置加载失败: {str(e)}")
            self.log(f"数据库配置加载失败: {str(e)}", "fail")

    def check_pages_exist(self):
        """检查页面文件是否存在"""
        self.log("", "title")
        self.log("📄 检查页面文件", "title")
        self.log("", "title")

        pages_dir = self.root / "ui" / "pages"
        expected_pages = [
            "__init__.py",
            "dashboard_page.py",
            "watermark_page.py",
        ]

        for page in expected_pages:
            page_path = pages_dir / page
            if page_path.exists():
                self.passed += 1
                self.log(f"页面 {page} 存在", "pass")
            else:
                self.failed += 1
                self.errors.append(f"页面 {page} 不存在")
                self.log(f"页面 {page} 不存在", "fail")

    def check_recycle_bin(self):
        """检查回收站"""
        self.log("", "title")
        self.log("🗑️ 检查回收站", "title")
        self.log("", "title")

        recycle_bin = self.root / ".recycle_bin"
        if recycle_bin.exists():
            files = list(recycle_bin.glob("*"))
            if files:
                self.log(f"回收站中有 {len(files)} 个文件:", "info")
                for f in sorted(files)[:10]:
                    self.log(f"  - {f.name}", "info")
                if len(files) > 10:
                    self.log(f"  ... 还有 {len(files) - 10} 个文件", "info")
                self.passed += 1
            else:
                self.log("回收站为空", "warning")
        else:
            self.log("回收站目录不存在", "warning")

    def check_dependencies(self):
        """检查依赖包"""
        self.log("", "title")
        self.log("📦 检查依赖包", "title")
        self.log("", "title")

        required = [
            "PySide6",
            "pymysql",
            "pypinyin",
            "smbprotocol",
        ]

        for pkg in required:
            try:
                importlib.import_module(pkg.lower().replace('-', '_'))
                self.passed += 1
                self.log(f"{pkg} ... 已安装", "pass")
            except ImportError:
                self.failed += 1
                self.errors.append(f"依赖包 {pkg} 未安装")
                self.log(f"{pkg} ... 未安装", "fail")

    def check_main_import(self):
        """检查主入口"""
        self.log("", "title")
        self.log("🚀 检查主入口", "title")
        self.log("", "title")

        try:
            # 检查 main.py 是否存在
            main_path = self.root / "main.py"
            if main_path.exists():
                self.passed += 1
                self.log("main.py 存在", "pass")

                # 检查是否能导入 MainWindow
                from ui.main_window import MainWindow
                self.passed += 1
                self.log("MainWindow 导入成功", "pass")
            else:
                self.failed += 1
                self.errors.append("main.py 不存在")
                self.log("main.py 不存在", "fail")
        except Exception as e:
            self.failed += 1
            self.errors.append(f"MainWindow 导入失败: {str(e)}")
            self.log(f"MainWindow 导入失败: {str(e)}", "fail")

    def run(self):
        """运行所有检查"""
        print("")
        print("=" * 70)
        print("🔍 项目自检开始")
        print("=" * 70)
        print("")

        self.check_recycle_bin()
        self.check_dependencies()
        self.check_imports()
        self.check_config()
        self.check_pages_exist()
        self.check_main_import()

        # 打印总结
        print("")
        print("=" * 70)
        print("📊 自检结果")
        print("=" * 70)
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")

        if self.errors:
            print("\n❌ 错误详情:")
            for err in self.errors:
                print(f"  - {err}")

        if self.failed == 0:
            print("\n🎉 所有检查通过！项目可以正常运行")
        else:
            print(f"\n⚠️ 有 {self.failed} 项检查失败，请查看上面的错误详情")

        print("=" * 70)

        return self.failed == 0


def main():
    """主函数"""
    os.chdir(Path(__file__).parent)
    checker = SelfChecker()
    success = checker.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()