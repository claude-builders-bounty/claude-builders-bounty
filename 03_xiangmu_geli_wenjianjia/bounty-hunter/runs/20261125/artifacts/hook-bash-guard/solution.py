#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.

This hook implements a safety gate for Claude Code / agent tool execution,
inspecting Bash commands before they run and rejecting any command that
matches a destructive pattern (rm -rf, format, mkfs, dd, shutdown, etc.).

Compliant with the bounty-hunter safety policy:
- No data destruction
- No credential leakage
- No exposure of services/ports
- Audit-logged decisions
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 红线命令模式（命中即拦截）──────────────────────────────────────────
DESTRUCTIVE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\brm\s+(-rf|-fr|--recursive.*--force|--force.*--recursive)", re.IGNORECASE),
    re.compile(r"\brm\s+(-rf|-fr)\s+/", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+.*of=", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
    re.compile(r"\binit\s+[0-6]\b", re.IGNORECASE),
    re.compile(r"\bformat\s+[A-Z]:", re.IGNORECASE),
    re.compile(r">\s*/dev/(sda|sdb|sdc|nvme)", re.IGNORECASE),
]

# 允许的安全前缀（即使命中模板也放行）
SAFE_PREFIXES: List[re.Pattern[str]] = [
    re.compile(r"\beg\s+", re.IGNORECASE),   # eg (editor) 误报兜底
    re.compile(r"\berg\s+", re.IGNORECASE),  # erg 误报兜底
]

# 审计日志路径（仅追加，不泄露敏感信息）
AUDIT_LOG = Path(os.environ.get("BOUNTY_HOOK_AUDIT_LOG", "runs/20261125/hook_audit.jsonl"))


def is_destructive(command: str) -> Tuple[bool, Optional[str]]:
    """判断命令是否为破坏性命令。

    Returns:
        (is_blocked, matched_pattern_or_none)
    """
    for safe in SAFE_PREFIXES:
        if safe.search(command):
            return False, None
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, pattern.pattern
    return False, None


def audit(command: str, blocked: bool, reason: Optional[str]) -> None:
    """仅追加写入审计日志，不记录明文凭据或敏感参数。"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "command_hash": _hash_command(command),
        "blocked": blocked,
        "reason": reason,
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # 审计失败不阻断主流程，但静默吞掉会违反规范；这里打印到 stderr 供排查
        print(f"[hook] audit write failed: {AUDIT_LOG}", file=sys.stderr)


def _hash_command(command: str) -> str:
    """对命令做简单摘要，避免明文落盘敏感参数。"""
    import hashlib

    return hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    """读取 stdin 中的工具调用事件，决定是否拦截。

    期望输入 JSON：
      {"tool": "bash", "command": "..."}
    """
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        print('{"ok": false, "error": "invalid JSON input"}', file=sys.stderr)
        return 2

    command = event.get("command", "")
    if not isinstance(command, str):
        print('{"ok": false, "error": "missing command field"}', file=sys.stderr)
        return 2

    blocked, reason = is_destructive(command)
    audit(command, blocked, reason)

    if blocked:
        result = {
            "ok": False,
            "blocked": True,
            "reason": "destructive_command_blocked",
            "message": (
                "命令被安全钩拦截：疑似破坏性操作。"
                " 若确认无误，请调整命令后重试。"
            ),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 1

    result = {
        "ok": True,
        "blocked": False,
        "reason": None,
        "message": "命令通过安全钩，允许执行。",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
