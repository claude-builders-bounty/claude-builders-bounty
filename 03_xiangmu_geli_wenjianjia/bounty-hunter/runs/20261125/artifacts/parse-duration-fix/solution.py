"""
parse_duration 修复：支持 days (d) 单位

题目: [BOUNTY $50] parse_duration drops the days (d) unit
平台: github_bounties_public
类型: Bug 修复 / Python
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Optional


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """解析持续时间字符串，支持 h/m/s/d 单位。

    修复前：parse_duration 仅识别 h/m/s，遇到 'd'（天）单位时丢弃或报错。
    修复后：支持 'd' 单位，例如 "2d3h30m" -> timedelta(days=2, hours=3, minutes=30)。

    支持的格式示例:
        "2d"         -> 2 天
        "3h"         -> 3 小时
        "30m"        -> 30 分钟
        "45s"        -> 45 秒
        "2d3h30m"    -> 2 天 3 小时 30 分钟
        "1d5s"       -> 1 天 5 秒
    """
    if not duration_str or not isinstance(duration_str, str):
        return None

    duration_str = duration_str.strip().lower()
    if not duration_str:
        return None

    # 解析 <数字><单位> 的片段，单位可为 d/h/m/s
    pattern = re.compile(r"(\d+(?:\.\d+)?)\s*([dhms])")
    matches = pattern.findall(duration_str)

    if not matches:
        return None

    # 校验：串联后的片段应覆盖整个字符串（忽略空白）
    reconstructed = "".join(f"{num}{unit}" for num, unit in matches)
    if reconstructed.replace(" ", "") != duration_str.replace(" ", ""):
        return None

    days = hours = minutes = seconds = 0.0
    for num_str, unit in matches:
        value = float(num_str)
        if unit == "d":
            days += value
        elif unit == "h":
            hours += value
        elif unit == "m":
            minutes += value
        elif unit == "s":
            seconds += value

    return timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


def parse_duration_to_seconds(duration_str: str) -> Optional[float]:
    """解析持续时间并返回总秒数。"""
    td = parse_duration(duration_str)
    if td is None:
        return None
    return td.total_seconds()


if __name__ == "__main__":
    # 快速自测
    cases = [
        ("2d", 172800.0),
        ("3h", 10800.0),
        ("30m", 1800.0),
        ("45s", 45.0),
        ("2d3h30m", 185400.0),
        ("1d5s", 86405.0),
        ("0.5d", 43200.0),
    ]
    for inp, expected in cases:
        result = parse_duration_to_seconds(inp)
        status = "OK" if result == expected else f"FAIL (got {result})"
        print(f"parse_duration({inp!r}) = {result} 期望 {expected} {status}")
