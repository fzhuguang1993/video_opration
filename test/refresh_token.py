#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刷新快手 Token - 使用 refresh_token 获取新的两个 token
并自动回写到 config.py
"""

import requests
import json
import re
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置
from config import KUAISHOU_APP_ID, KUAISHOU_SECRET, KUAISHOU_REFRESH_TOKEN


def update_config_file(access_token, refresh_token):
    """更新 config.py 中的两个 token"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换 KUAISHOU_ACCESS_TOKEN
        pattern_access = r"(KUAISHOU_ACCESS_TOKEN\s*=\s*)'[^']*'"
        replacement_access = f"KUAISHOU_ACCESS_TOKEN = '{access_token}'"
        content = re.sub(pattern_access, replacement_access, content)

        # 替换 KUAISHOU_REFRESH_TOKEN
        pattern_refresh = r"(KUAISHOU_REFRESH_TOKEN\s*=\s*)'[^']*'"
        replacement_refresh = f"KUAISHOU_REFRESH_TOKEN = '{refresh_token}'"
        content = re.sub(pattern_refresh, replacement_refresh, content)

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 已更新 config.py")
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False


def refresh_token():
    """使用 refresh_token 刷新获取新的两个 token"""
    print("=" * 60)
    print("🔄 刷新 Token")
    print("=" * 60)
    print(f"📌 App ID: {KUAISHOU_APP_ID}")
    print(f"📌 当前 Refresh Token: {KUAISHOU_REFRESH_TOKEN[:20]}...")
    print("-" * 60)

    url = 'https://ad.e.kuaishou.com/rest/openapi/oauth2/authorize/refresh_token'
    payload = {
        'app_id': KUAISHOU_APP_ID,
        'secret': KUAISHOU_SECRET,
        'refresh_token': KUAISHOU_REFRESH_TOKEN
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        print("📥 响应结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("-" * 60)

        if result.get('code') == 0:
            data = result.get('data', {})
            new_access_token = data.get('access_token')
            new_refresh_token = data.get('refresh_token')
            expires_in = data.get('expires_in', 0)

            print("✅ 刷新成功！")
            print("=" * 60)
            print(f"🔑 新 Access Token: {new_access_token}")
            print(f"🔄 新 Refresh Token: {new_refresh_token}")
            print(f"⏰ 过期时间: {expires_in} 秒 ({expires_in // 3600} 小时)")
            print("=" * 60)

            # 回写到 config.py
            print("\n📝 正在回写 config.py...")
            if update_config_file(new_access_token, new_refresh_token):
                print("✅ Token 已更新到 config.py")
            else:
                print("⚠️ 请手动更新 config.py")

            return new_access_token, new_refresh_token
        else:
            print(f"❌ 刷新失败: {result.get('message')}")
            return None, None

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None, None


def main():
    """模拟 access_token 过期，用 refresh_token 刷新"""
    print("=" * 60)
    print("🚀 模拟 Token 过期刷新")
    print("=" * 60)
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # 检查 refresh_token 是否存在
    if not KUAISHOU_REFRESH_TOKEN:
        print("❌ config.py 中没有 refresh_token")
        return

    print("📌 当前 config.py 中的 refresh_token:")
    print(f"   {KUAISHOU_REFRESH_TOKEN}")
    print()
    print("🔄 开始刷新...")
    print()

    # 刷新 token
    new_access, new_refresh = refresh_token()

    if new_access and new_refresh:
        print("\n" + "=" * 60)
        print("✅ 刷新完成！")
        print("=" * 60)
        print("📋 新的 Token 已保存到 config.py")
        print(f"🔑 Access Token: {new_access}")
        print(f"🔄 Refresh Token: {new_refresh}")
        print("=" * 60)
    else:
        print("\n❌ 刷新失败")


if __name__ == '__main__':
    main()