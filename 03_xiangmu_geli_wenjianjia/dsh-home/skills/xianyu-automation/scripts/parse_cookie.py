#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 字符串 <-> dict 转换工具
用于闲鱼 Cookie 格式转换
"""

import sys
import json


def parse_cookie_string(cookie_str: str) -> dict:
    """将 cookie 字符串解析为 dict"""
    cookie_dict = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookie_dict[k.strip()] = v.strip()
    return cookie_dict


def format_cookie_dict(cookie_dict: dict) -> str:
    """将 cookie dict 格式化为字符串"""
    return "; ".join(f"{k}={v}" for k, v in cookie_dict.items())


def validate_cookie_dict(cookie_dict: dict) -> tuple:
    """验证 cookie dict 是否包含必需字段"""
    required = ["_m_h5_tk", "_m_h5_tk_enc", "cookie2", "t", "cna", "xlly_s"]
    missing = [field for field in required if field not in cookie_dict]
    return len(missing) == 0, missing


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python parse_cookie.py parse 'cookie字符串'")
        print("  python parse_cookie.py format '{\"k\": \"v\"}'")
        print("  python parse_cookie.py validate 'cookie字符串'")
        sys.exit(1)

    action = sys.argv[1]

    if action == "parse":
        if len(sys.argv) < 3:
            print("错误: 需要提供 cookie 字符串")
            sys.exit(1)
        cookie_str = sys.argv[2]
        result = parse_cookie_string(cookie_str)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif action == "format":
        if len(sys.argv) < 3:
            print("错误: 需要提供 JSON 字符串")
            sys.exit(1)
        cookie_dict = json.loads(sys.argv[2])
        print(format_cookie_dict(cookie_dict))

    elif action == "validate":
        if len(sys.argv) < 3:
            print("错误: 需要提供 cookie 字符串")
            sys.exit(1)
        cookie_str = sys.argv[2]
        cookie_dict = parse_cookie_string(cookie_str)
        valid, missing = validate_cookie_dict(cookie_dict)
        if valid:
            print("✅ Cookie 验证通过，包含所有必需字段")
        else:
            print(f"❌ Cookie 缺少必需字段: {', '.join(missing)}")
        print(f"字段总数: {len(cookie_dict)}")

    else:
        print(f"未知操作: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()