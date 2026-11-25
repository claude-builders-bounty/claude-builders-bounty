#!/usr/bin/env python3
"""
Fix for Chinese numeral chapter heading detection in book-to-skill extraction.
牧神记 uses format: "=第一章 天黑别出门===" (with = signs and Chinese numerals)
This script patches the extraction to handle this format.
"""

import re

# Add to find_chapters() patterns list in book_to_skill/extraction.py or gen script:
CHINESE_CHAPTER_PATTERNS = [
    # =第一章 天黑别出门===
    r'^=第\s*([一二三四五六七八九十百千万\d]+)\s*章\s*={2,3}\s*(.*)$',
    # 第 一 章 标题 (with spaces)
    r'^第\s*([一二三四五六七八九十百千万\d]+)\s*章\s+(.+)$',
    # 第N章标题 (no space)
    r'^第([一二三四五六七八九十百千万\d]+)章\s*(.*)$',
]

CHINESE_DIGITS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000
}

def chinese_num_to_int(chinese_num: str) -> int:
    """Convert Chinese numerals to integer. Handles: 一, 十一, 二十, 一百二, 一千三百 etc."""
    if chinese_num.isdigit():
        return int(chinese_num)
    
    result = 0
    temp = 0
    for char in chinese_num:
        if char in CHINESE_DIGITS:
            val = CHINESE_DIGITS[char]
            if val >= 10:
                if temp == 0:
                    temp = 1
                result += temp * val
                temp = 0
            else:
                temp = temp * 10 + val
    result += temp
    return result if result > 0 else 1

# Usage in extraction:
# chap_num = chinese_num_to_int(match.group(1))
# title = match.group(2).strip() if match.group(2) else f"Chapter {chap_num}"