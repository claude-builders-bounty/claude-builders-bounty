#!/usr/bin/env python3
"""
pre-tool-use hook - 拦截危险bash命令
安装: cp pre-tool-use.py ~/.claude/hooks/
"""

import re, sys

DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf 禁止: 请使用安全的文件删除方式'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE 禁止: 请使用 DROP TABLE IF EXISTS + 备份'),
    (r'\bgit\s+push\s+--force\b', 'git push --force 禁止: 请使用 --force-with-lease'),
    (r'\bTRUNCATE\b', 'TRUNCATE 禁止: 请先备份数据'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM 无WHERE条件禁止: 请添加WHERE子句'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE 禁止: 危险操作'),
    (r'\bformat\s+(C|D):\b', '格式化磁盘禁止'),
    (r'\bdd\s+if=', 'dd 命令禁止: 可能覆写磁盘'),
    (r'>\s*/dev/sd[a-z]', '直接写入块设备禁止'),
    (r'\bchmod\s+777\b', 'chmod 777 不安全'),
    (r'\bcurl\s+.*\||\bwget\s+.*\|', '管道执行远程脚本禁止: 请先审查内容'),
    (r'\bsudo\s+rm\b', 'sudo rm 禁止'),
]

def check_command(cmd: str) -> list:
    warnings = []
    for pattern, msg in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            warnings.append(msg)
    return warnings

def main():
    if len(sys.argv) < 2:
        print("Usage: pre-tool-use.py <command>")
        sys.exit(1)
    
    cmd = " ".join(sys.argv[1:])
    warnings = check_command(cmd)
    
    if warnings:
        print("⚠️  HOOK BLOCKED: Dangerous command detected!")
        for w in warnings:
            print("  - %s" % w)
        print("\nCommand: %s" % cmd[:80])
        print("To override, add: #allow-dangerous at the end of the command")
        sys.exit(1)
    
    print("✅ Command passed safety check")

if __name__ == "__main__":
    main()
