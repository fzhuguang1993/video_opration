#!/usr/bin/env python3
"""
电影运营项目 - 结构查看和代码审查工具（排除虚拟环境）
专为 /Users/leiliang/PycharmProjects/movie_opration 定制
"""

import os
import sys
import ast
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter


class MovieProjectChecker:
    def __init__(self, root_path='/Users/leiliang/PycharmProjects/movie_opration'):
        self.root_path = Path(root_path).resolve()
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'python_files': 0,
            'python_lines': 0,
            'empty_files': 0,
            'file_types': defaultdict(int),
            'size_by_type': defaultdict(int),
            'func_count': 0,
            'class_count': 0,
            'import_count': 0,
            'imports_list': [],
            'errors': [],
            'warnings': []
        }
        # 关键：排除虚拟环境、第三方库、构建产物等
        self.ignore_dirs = {
            '.git', '__pycache__', 'venv', 'env', '.env',
            'node_modules', 'dist', 'build', '.idea', '.vscode',
            'logs', 'temp', 'tmp', '.pytest_cache',
            '.venv',  # 虚拟环境
            'Lib', 'lib', 'include', 'Scripts', 'bin',  # 虚拟环境子目录
            'site-packages', 'dist-packages',  # 第三方库
            'tests', 'test',  # 测试目录（可选，看你需要）
            'docs', 'doc',  # 文档目录
            'examples', 'example',  # 示例目录
            '.git', '.svn', '.hg',  # 版本控制
            '__pycache__', '.mypy_cache', '.pytest_cache',  # 缓存
            'build', 'dist', 'egg-info',  # 构建产物
            'node_modules', 'bower_components'  # 前端依赖
        }
        self.ignore_files = {
            '.DS_Store', '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.dylib', '*.dll',  # 二进制文件
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp',  # 图片
            '*.qm', '*.ts',  # Qt文件
            '*.qml',  # QML文件
            '*.sip',  # SIP文件
            '*.txt', '*.md', '*.rst',  # 文档（可选）
            '*.json', '*.xml', '*.yaml', '*.yml'  # 配置文件（可选）
        }
        self.project_tree = []
        self.only_project_files = True  # 只统计项目文件

    def _is_venv_path(self, path):
        """检查路径是否在虚拟环境中"""
        path_str = str(path)
        # 检查是否包含虚拟环境相关路径
        venv_indicators = [
            '.venv', 'venv', 'env', '.env',
            'site-packages', 'dist-packages',
            'Lib/site-packages', 'lib/python',
            'Scripts', 'bin'
        ]
        # 检查路径中的每个部分
        parts = path.parts
        for part in parts:
            if part in self.ignore_dirs:
                return True
            # 检查是否包含 site-packages 等
            if 'site-packages' in part or 'dist-packages' in part:
                return True
            if part.startswith('python') and len(part) > 6:  # python3.9 等
                if 'lib' in parts or 'Lib' in parts:
                    return True
        return False

    def scan(self):
        """扫描项目结构"""
        print(f"\n{'=' * 70}")
        print(f"🎬 电影运营项目结构扫描（仅项目代码）")
        print(f"📁 路径: {self.root_path}")
        print(f"{'=' * 70}\n")

        # 遍历生成树形结构
        self._generate_tree(self.root_path, 0, set())

        # 统计信息
        for root, dirs, files in os.walk(self.root_path):
            # 过滤忽略目录
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            # 检查是否在虚拟环境中
            root_path = Path(root)
            if self._is_venv_path(root_path):
                dirs[:] = []  # 清空子目录，不继续遍历
                continue

            rel_root = Path(root).relative_to(self.root_path)

            for file in files:
                if file in self.ignore_files or file.startswith('.'):
                    continue

                # 跳过二进制文件
                if file.endswith(('.so', '.dylib', '.dll', '.pyd')):
                    continue

                file_path = Path(root) / file
                rel_path = rel_root / file
                self.stats['total_files'] += 1

                try:
                    size = file_path.stat().st_size
                    ext = file_path.suffix or 'no_ext'
                    self.stats['file_types'][ext] += 1
                    self.stats['size_by_type'][ext] += size
                except:
                    continue

                # 只分析项目Python文件（不分析第三方库）
                if ext == '.py' or file == 'setup.py':
                    # 确保不是第三方库
                    if 'site-packages' not in str(file_path) and 'dist-packages' not in str(file_path):
                        self._analyze_python(file_path, rel_path)

    def _generate_tree(self, path, level, visited):
        """生成树形结构（限制深度防止输出过多）"""
        if level > 4:  # 限制深度
            return

        if path in visited:
            return
        visited.add(path)

        indent = '  ' * level
        if level == 0:
            self.project_tree.append(f"📁 {path.name}/")
        else:
            self.project_tree.append(f"{indent}├── 📁 {path.name}/")

        try:
            items = sorted([p for p in path.iterdir()
                            if not p.name.startswith('.')
                            and p.name not in self.ignore_dirs
                            and not self._is_venv_path(p)])

            dirs = [p for p in items if p.is_dir()]
            files = [p for p in items if p.is_file()
                     and p.name not in self.ignore_files
                     and not p.name.endswith(('.so', '.dylib', '.dll', '.pyd'))]

            # 显示目录
            for i, d in enumerate(dirs):
                prefix = '├──' if i < len(dirs) - 1 or files else '└──'
                self.project_tree.append(f"{indent}  {prefix} 📁 {d.name}/")
                self._generate_tree(d, level + 1, visited)

            # 显示文件（只显示前3个）
            for i, f in enumerate(files[:3]):
                prefix = '├──' if i < len(files[:3]) - 1 else '└──'
                try:
                    size_kb = f.stat().st_size / 1024
                    self.project_tree.append(f"{indent}  {prefix} 📄 {f.name} ({size_kb:.1f}KB)")
                except:
                    self.project_tree.append(f"{indent}  {prefix} 📄 {f.name}")

            if len(files) > 3:
                self.project_tree.append(f"{indent}  └── ... 还有 {len(files) - 3} 个文件")

        except PermissionError:
            pass

    def _analyze_python(self, file_path, rel_path):
        """分析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            self.stats['errors'].append(f"编码错误: {rel_path}")
            return
        except Exception as e:
            self.stats['errors'].append(f"读取错误 {rel_path}: {str(e)}")
            return

        lines = content.split('\n')
        self.stats['python_files'] += 1
        self.stats['python_lines'] += len(lines)

        if len(lines) == 0:
            self.stats['empty_files'] += 1

        # 只分析项目根目录下的文件（排除虚拟环境）
        if 'site-packages' in str(file_path) or 'dist-packages' in str(file_path):
            return

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.stats['func_count'] += 1
                    if not ast.get_docstring(node):
                        # 只在项目文件中警告
                        if not self._is_venv_path(file_path):
                            self.stats['warnings'].append(f"{rel_path}:{node.lineno} 函数 {node.name} 缺少docstring")
                elif isinstance(node, ast.ClassDef):
                    self.stats['class_count'] += 1
                    if not ast.get_docstring(node):
                        if not self._is_venv_path(file_path):
                            self.stats['warnings'].append(f"{rel_path}:{node.lineno} 类 {node.name} 缺少docstring")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    self.stats['import_count'] += 1
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.stats['imports_list'].append(alias.name)
                    else:
                        module = node.module or ''
                        for alias in node.names:
                            self.stats['imports_list'].append(f"{module}.{alias.name}")

        except SyntaxError as e:
            self.stats['errors'].append(f"语法错误 {rel_path}: 第{e.lineno}行 - {e.msg}")
        except Exception as e:
            self.stats['errors'].append(f"解析错误 {rel_path}: {str(e)}")

    def print_tree(self):
        """打印目录树"""
        print("\n📂 项目结构（仅项目代码）:")
        print("-" * 70)
        for line in self.project_tree[:100]:
            print(line)
        if len(self.project_tree) > 100:
            print(f"\n... 还有 {len(self.project_tree) - 100} 行结构信息")
        print("-" * 70)

    def print_report(self):
        """打印报告"""
        print(f"\n{'=' * 70}")
        print("📊 项目统计报告（仅项目代码）")
        print(f"{'=' * 70}\n")

        print("📄 文件统计:")
        print(f"  - 项目文件总数: {self.stats['total_files']}")
        print(f"  - Python文件数: {self.stats['python_files']}")
        print(f"  - 空文件: {self.stats['empty_files']}")

        print(f"\n📝 代码统计:")
        print(f"  - Python总行数: {self.stats['python_lines']:,}")
        print(f"  - 函数数量: {self.stats['func_count']}")
        print(f"  - 类数量: {self.stats['class_count']}")
        print(f"  - 导入语句: {self.stats['import_count']}")

        print(f"\n📂 文件类型分布 (Top 10):")
        sorted_types = sorted(self.stats['file_types'].items(),
                              key=lambda x: -x[1])[:10]
        for ext, count in sorted_types:
            size_mb = self.stats['size_by_type'][ext] / (1024 * 1024)
            ext_name = ext or '无扩展名'
            print(f"  - {ext_name}: {count} 个, {size_mb:.2f} MB")

        if self.stats['imports_list']:
            top_imports = Counter(self.stats['imports_list']).most_common(10)
            print(f"\n📦 项目使用的主要库 (Top 10):")
            for imp, count in top_imports:
                print(f"  - {imp}: {count} 次")

        # 检查项目主要模块
        print(f"\n📋 项目主要模块:")
        project_modules = ['main.py', 'main_window.py', 'config.py', 'movie_work_space.py']
        for module in project_modules:
            if (self.root_path / module).exists():
                print(f"  ✅ {module}")
            else:
                print(f"  ❌ {module} (不存在)")

        # 检查子模块
        sub_modules = ['auth', 'utils', 'widgets', 'worker']
        print(f"\n📁 子模块:")
        for sub in sub_modules:
            if (self.root_path / sub).exists():
                print(f"  ✅ {sub}/")
            else:
                print(f"  ❌ {sub}/ (不存在)")

        if self.stats['warnings']:
            print(f"\n⚠️  警告 (显示前20个):")
            for warn in self.stats['warnings'][:20]:
                print(f"  - {warn}")
            if len(self.stats['warnings']) > 20:
                print(f"  ... 还有 {len(self.stats['warnings']) - 20} 个警告")

        if self.stats['errors']:
            print(f"\n❌ 错误 ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:10]:
                print(f"  - {err}")
            if len(self.stats['errors']) > 10:
                print(f"  ... 还有 {len(self.stats['errors']) - 10} 个错误")

        # 项目健康度评估
        print(f"\n{'=' * 70}")
        print("🏥 项目健康度评估:")
        health_score = 100

        if self.stats['errors']:
            health_score -= min(len(self.stats['errors']) * 5, 30)
        if self.stats['warnings']:
            # 警告太多也不好
            health_score -= min(len(self.stats['warnings']) // 10, 20)
        if self.stats['python_lines'] > 5000:
            health_score -= 5
        if self.stats['func_count'] > 0 and self.stats['class_count'] == 0:
            health_score -= 10

        health_score = max(0, min(100, health_score))

        if health_score >= 80:
            status = "✅ 健康"
        elif health_score >= 60:
            status = "⚠️  一般"
        else:
            status = "❌ 需要改善"

        print(f"  - 健康评分: {health_score}/100")
        print(f"  - 状态: {status}")

        if health_score < 80:
            print(f"\n💡 改进建议:")
            if self.stats['errors']:
                print("  - 修复所有语法和编码错误")
            if len(self.stats['warnings']) > 50:
                print("  - 为函数和类添加文档字符串 (docstring)")
            if self.stats['class_count'] == 0 and self.stats['func_count'] > 10:
                print("  - 考虑使用类来组织相关功能")
            if self.stats['python_files'] > 10:
                print("  - 考虑将大文件拆分成更小的模块")

        print(f"\n{'=' * 70}")
        print("✅ 扫描完成")
        print(f"{'=' * 70}\n")

    def export_json(self, output_file='movie_project_stats_clean.json'):
        """导出JSON格式"""
        data = {
            'project': str(self.root_path),
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_files': self.stats['total_files'],
                'python_files': self.stats['python_files'],
                'python_lines': self.stats['python_lines'],
                'functions': self.stats['func_count'],
                'classes': self.stats['class_count'],
                'imports': self.stats['import_count'],
                'errors': self.stats['errors'],
                'warnings': self.stats['warnings'][:50]
            },
            'file_types': dict(self.stats['file_types']),
            'top_imports': dict(Counter(self.stats['imports_list']).most_common(20))
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"📤 导出统计到: {output_file}")


def main():
    # 你的项目路径
    project_path = '/Users/leiliang/PycharmProjects/movie_opration'

    if not os.path.exists(project_path):
        print(f"❌ 路径不存在: {project_path}")
        sys.exit(1)

    checker = MovieProjectChecker(project_path)
    checker.scan()
    checker.print_tree()
    checker.print_report()
    checker.export_json()


if __name__ == '__main__':
    main()