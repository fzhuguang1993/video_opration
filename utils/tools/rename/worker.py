# utils/tools/rename/worker.py
"""重命名后台线程 - RenameWorker"""

import os
from PySide6.QtCore import QThread, Signal


class RenameWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(bool, str, dict)  # 增加 dict 返回详细结果

    def __init__(self, file_paths: list, pattern: list, regex_enabled: bool = False):
        super().__init__()
        self.file_paths = file_paths
        self.pattern = pattern
        self.regex_enabled = regex_enabled
        self._is_running = True
        self.results = []  # 存储每个文件的执行结果

    def stop(self):
        self._is_running = False

    def _to_letter(self, n: int, upper: bool = True) -> str:
        result = ""
        while n > 0:
            n -= 1
            result = chr((n % 26) + (ord('A') if upper else ord('a'))) + result
            n //= 26
        return result

    def _to_roman(self, n: int) -> str:
        roman_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                     (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                     (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
        result = ""
        num = n
        for value, symbol in roman_map:
            while num >= value:
                result += symbol
                num -= value
        return result

    def _to_greek(self, n: int) -> str:
        greek = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
                 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']
        if n <= len(greek):
            return greek[n - 1]
        result = ""
        while n > 0:
            n -= 1
            result = greek[n % 24] + result
            n //= 24
        return result

    def _get_next_value(self, rule: dict, index: int) -> str:
        if rule['type'] == '数字':
            return str(rule['start_num'] + index).zfill(rule['padding'])
        elif rule['type'] == '大写字母':
            return self._to_letter(rule['start_num'] + index, upper=True)
        elif rule['type'] == '小写字母':
            return self._to_letter(rule['start_num'] + index, upper=False)
        elif rule['type'] == '罗马数字':
            return self._to_roman(rule['start_num'] + index)
        elif rule['type'] == '希腊字母':
            return self._to_greek(rule['start_num'] + index)
        return ""

    def _build_name(self, index: int, ext: str, original_name: str = "") -> str:
        parts = []
        for rule in self.pattern:
            if rule['type'] == '扩展名':
                continue
            elif rule['type'] == '原文件名':
                if original_name:
                    parts.append(original_name)
                else:
                    parts.append("{原文件名}")
            elif rule['type'] in ['数字', '大写字母', '小写字母', '罗马数字', '希腊字母']:
                parts.append(self._get_next_value(rule, index))
            else:
                parts.append(rule['text'])
        return ''.join(parts) + ext

    def run(self):
        total = len(self.file_paths)
        renamed = 0
        failed = 0
        self.results = []

        for idx, file_path in enumerate(self.file_paths, 1):
            if not self._is_running:
                break

            dir_path = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1]
            original_base = os.path.splitext(os.path.basename(file_path))[0]
            new_name = self._build_name(idx - 1, ext, original_base)
            new_path = os.path.join(dir_path, new_name)

            # 记录结果
            result = {
                "old_path": file_path,
                "new_path": new_path,
                "old_name": os.path.basename(file_path),
                "new_name": new_name,
                "status": "skipped"  # 默认跳过
            }

            if os.path.basename(file_path) == new_name:
                renamed += 1
                result["status"] = "skipped"
                result["reason"] = "文件名未变化"
                self.results.append(result)
                continue

            if os.path.exists(new_path):
                failed += 1
                result["status"] = "failed"
                result["reason"] = "目标文件已存在"
                self.results.append(result)
                continue

            try:
                os.rename(file_path, new_path)
                renamed += 1
                result["status"] = "success"
                result["reason"] = ""
                self.results.append(result)
            except Exception as e:
                failed += 1
                result["status"] = "failed"
                result["reason"] = str(e)
                self.results.append(result)

        self.finished.emit(
            True,
            f"完成！成功: {renamed}，失败: {failed}",
            {
                "total": total,
                "renamed": renamed,
                "failed": failed,
                "results": self.results,
                "pattern": self.pattern
            }
        )