#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取快手 Token"""

import requests
import json
import sys

sys.path.append('.')
from config import KUAISHOU_APP_ID, KUAISHOU_SECRET

# 从浏览器获取的 auth_code
AUTH_CODE = "0e28e154b7959150185cdb8ec2c91ad8"


def get_token():
    url = 'https://ad.e.kuaishou.com/rest/openapi/oauth2/authorize/access_token'
    payload = {
        'app_id': KUAISHOU_APP_ID,
        'secret': KUAISHOU_SECRET,
        'grant_type': 'authorization_code',
        'auth_code': AUTH_CODE
    }

    response = requests.post(url, json=payload)
    result = response.json()

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get('code') == 0:
        data = result.get('data', {})
        print("\n" + "=" * 60)
        print("✅ 获取成功！请复制以下内容更新 config.py：")
        print("=" * 60)
        print(f"KUAISHOU_ACCESS_TOKEN = '{data.get('access_token')}'")
        print(f"KUAISHOU_REFRESH_TOKEN = '{data.get('refresh_token')}'")
        print("=" * 60)
    else:
        print(f"\n❌ 失败: {result.get('message')}")


if __name__ == '__main__':
    if AUTH_CODE == "你的auth_code":
        print("请先在浏览器访问：")
        print(
            f"https://ad.e.kuaishou.com/rest/openapi/oauth2/authorize?app_id={KUAISHOU_APP_ID}&response_type=code&scope=1")
        print("\n登录后从 URL 中获取 code 参数，替换 AUTH_CODE 变量")
    else:
        get_token()