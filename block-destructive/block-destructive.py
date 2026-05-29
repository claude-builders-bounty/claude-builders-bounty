#!/usr/bin/env python3
"""
block-destructive — Pre-tool-use hook for Claude Code

Blocks destructive bash commands before execution.
Logs all blocked attempts with timestamp, command, and project path.

Install: Copy to ~/.claude/hooks/block-destructive (or .py)
"""

import json
import os
import sys
import re
import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_NAME = "block-destructive"

# 需要拦截的破坏性命令模式
BLOCK_PATTERNS = [
    # rm -rf (递归强制删除)
    r'\brm\s+(-[a-z]*[rR][a-z]*\s*)?-?f\b',
    # DROP TABLE (删除数据库表)
    r'\bDROP\s+TABLE\b',
    # git push --force (强制推送)
    r'\bgit\s+push\s+.*--force\b',
    r'\bgit\s+push\s+.*-f\b',
    # TRUNCATE (清空数据库表)
    r'\bTRUNCATE\b',
    # DELETE FROM 不含 WHERE
    r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',
    # 危险管道：直接覆盖系统文件
    r'>\s*/etc/',
    r'>\s*/boot/',
]


def should_block(command: str) -> tuple[bool, str]:
    """
    检查命令是否应被拦截。
    返回 (should_block, reason)
    """
    lower_cmd = command.lower()
    
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, lower_cmd, re.IGNORECASE):
            # 特别处理 DELETE FROM: 检查是否有 WHERE
            if 'delete from' in lower_cmd and 'where' in lower_cmd:
                continue  # 有 WHERE 子句，放行
            return True, f"Matched pattern: {pattern}"
    
    return False, ""


def log_block(command: str, reason: str):
    """记录拦截日志"""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.getcwd()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] BLOCKED | reason={reason} | cwd={project_path} | cmd={command}\n")
    except Exception:
        pass  # 日志写入失败不阻塞流程


def main():
    # Claude Code hooks 通过 stdin 接收 JSON
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # 非 JSON 输入，直接放行
            sys.exit(0)
        
        data = json.loads(raw_input)
    except (json.JSONDecodeError, Exception):
        # 无法解析输入，放行
        sys.exit(0)
    
    # 提取命令
    command = ""
    if isinstance(data, dict):
        # 尝试多种可能的字段名
        command = data.get("command") or data.get("cmd") or data.get("args") or data.get("input") or ""
        if isinstance(command, list):
            command = " ".join(str(c) for c in command)
    
    if not command:
        sys.exit(0)  # 无可检查命令，放行
    
    # 检查是否应拦截
    block, reason = should_block(command)
    
    if block:
        log_block(command, reason)
        
        # 返回阻止响应的 JSON
        response = {
            "type": "block",
            "reason": (
                f"🚫 Command blocked by {HOOK_NAME} hook.\n"
                f"Reason: This command appears destructive: {reason}\n\n"
                f"If you're sure, use an alternative approach:\n"
                f"  - For rm: move files to trash instead\n"
                f"  - For DB: use a migration tool\n"
                f"  - For git: use --force-with-lease instead of --force\n\n"
                f"Blocked command: {command[:200]}"
            ),
            "level": "error"
        }
        print(json.dumps(response))
        sys.exit(1)
    else:
        # 放行
        sys.exit(0)


if __name__ == "__main__":
    main()
