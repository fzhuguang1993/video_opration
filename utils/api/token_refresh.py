#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快手 Token 刷新工具 - 核心功能
使用 refresh_token 获取新的两个 token，自动回写 config.py
"""

import requests
import json
import re
import os
import sys


def refresh_kuaishou_token():
    """
    使用 refresh_token 刷新获取新的 access_token 和 refresh_token
    自动回写 config.py
    返回: (new_access_token, new_refresh_token) 或 (None, None)
    """
    # 动态导入 config，避免循环依赖
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                               'config.py')

    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取配置值
    import re as regex
    app_id_match = regex.search(r"KUAISHOU_APP_ID\s*=\s*(\d+)", content)
    secret_match = regex.search(r"KUAISHOU_SECRET\s*=\s*'([^']*)'", content)
    refresh_token_match = regex.search(r"KUAISHOU_REFRESH_TOKEN\s*=\s*'([^']*)'", content)

    if not all([app_id_match, secret_match, refresh_token_match]):
        print("❌ 无法从 config.py 读取配置")
        return None, None

    app_id = int(app_id_match.group(1))
    secret = secret_match.group(1)
    refresh_token = refresh_token_match.group(1)

    if not refresh_token:
        print("❌ refresh_token 为空")
        return None, None

    # 调用快手 API 刷新 token
    url = 'https://ad.e.kuaishou.com/rest/openapi/oauth2/authorize/refresh_token'
    payload = {
        'app_id': app_id,
        'secret': secret,
        'refresh_token': refresh_token
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if result.get('code') != 0:
            print(f"❌ 刷新失败: {result.get('message')}")
            return None, None

        data = result.get('data', {})
        new_access_token = data.get('access_token')
        new_refresh_token = data.get('refresh_token')

        if not new_access_token:
            print("❌ 响应中没有 access_token")
            return None, None

        # 回写 config.py
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换 KUAISHOU_ACCESS_TOKEN
        content = regex.sub(
            r"(KUAISHOU_ACCESS_TOKEN\s*=\s*)'[^']*'",
            f"KUAISHOU_ACCESS_TOKEN = '{new_access_token}'",
            content
        )

        # 替换 KUAISHOU_REFRESH_TOKEN
        if new_refresh_token:
            content = regex.sub(
                r"(KUAISHOU_REFRESH_TOKEN\s*=\s*)'[^']*'",
                f"KUAISHOU_REFRESH_TOKEN = '{new_refresh_token}'",
                content
            )

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Token 刷新成功并已保存到 config.py")
        return new_access_token, new_refresh_token

    except Exception as e:
        print(f"❌ 刷新异常: {e}")
        return None, None