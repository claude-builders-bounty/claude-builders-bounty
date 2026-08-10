#!/usr/bin/env python3
"""Claude Code pre-tool-use hook：拦截危险 bash 命令。

用法（写入 ~/.claude/settings.json 的 hooks.pre_tool_use）：
  "hooks": {
    "pre_tool_use": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" } ] }
    ]
  }

输入：stdin 上的 JSON（Claude Code hook 规范）。
输出：JSON，含 hookSpecificOutput.decision = "block" | "approve"。
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# 危险模式：命令 → 说明
DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)+[^\s;|&]+", re.IGNORECASE), "rm -r 递归删除"),
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "rm -rf 强制递归删除"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE 删表"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE 清空表"),
    (re.compile(r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", re.IGNORECASE), "DELETE FROM 无 WHERE 条件"),
    (re.compile(r"\bgit\s+push\s+--force\b", re.IGNORECASE), "git push --force 强推覆盖远端"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard 丢弃工作区改动"),
    (re.compile(r"\bmkfs\.?\w*|format\s+[a-z]:", re.IGNORECASE), "格式化磁盘"),
    (re.compile(r"\bshutdown|reboot|poweroff\b", re.IGNORECASE), "关机/重启系统"),
]


def sanitize(value: str) -> str:
    return (value or "").replace("\n", " ").replace("\r", " ")[:500]


def log_blocked(command: str, reason: str, cwd: str) -> None:
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] reason={reason} cwd={cwd} cmd={sanitize(command)}\n")
    except OSError:
        pass  # 日志失败不影响拦截本身


def block(command: str, reason: str, cwd: str) -> dict:
    log_blocked(command, reason, cwd)
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "decision": "block",
            "reason": (
                f"危险命令被拦截：{reason}。\n"
                f"拦截的命令：`{sanitize(command)}`\n"
                "建议：改用安全方式（如先备份、带 WHERE 条件的 DELETE、普通 git push 等），"
                "或向用户确认后手工执行。"
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # 无法解析时放行，避免误伤

    tool_name = str(payload.get("tool_name", ""))
    if tool_name != "Bash":
        # 非 bash 工具不拦截
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command", ""))
    cwd = str(payload.get("cwd") or os.getcwd())

    if not command.strip():
        return 0

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            print(json.dumps(block(command, reason, cwd), ensure_ascii=False))
            return 0

    # 正常命令：approve 并允许
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "decision": "approve",
                    "reason": "命令安全，放行",
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
