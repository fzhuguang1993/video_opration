#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 config.py 添加 AUTH_CODE"""

import re
import os

# config.py 在项目根目录
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
AUTH_CODE = "我是你爷爷"


def update_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已存在 KUAISHOU_AUTH_CODE
    if 'KUAISHOU_AUTH_CODE' in content:
        # 如果存在则替换
        pattern = r"(KUAISHOU_AUTH_CODE\s*=\s*)'[^']*'"
        content = re.sub(pattern, f"KUAISHOU_AUTH_CODE = '{AUTH_CODE}'", content)
    else:
        # 如果不存在则在 KUAISHOU_REFRESH_TOKEN 后面添加
        pattern = r"(KUAISHOU_REFRESH_TOKEN\s*=\s*'[^']*')"
        replacement = f"\\1\nKUAISHOU_AUTH_CODE = '{AUTH_CODE}'"
        content = re.sub(pattern, replacement, content)

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已更新 {CONFIG_FILE}")
    print(f"   添加 KUAISHOU_AUTH_CODE = '{AUTH_CODE}'")


if __name__ == '__main__':
    update_config()