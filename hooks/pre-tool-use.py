#!/usr/bin/env python3
"""
pre-tool-use.py — Claude Code pre-tool-use hook

Intercepts dangerous bash commands before they run. Blocks patterns like:
  - rm -rf (recursive force delete)
  - DROP TABLE (SQL destructive)
  - git push --force (force push)
  - TRUNCATE (SQL mass delete)
  - DELETE FROM without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

# 危险模式匹配规则 —— 每条是一个 (编译后正则, 人类可读原因)
DANGEROUS_PATTERNS = [  # type: list[tuple[re.Pattern, str]]
    (re.compile(r'\brm\s+(-[rf]+|-[rf]+\s)|-rf\b'), "rm -rf: 递归强制删除"),
    (re.compile(r'\bdrop\s+table\b', re.IGNORECASE), "DROP TABLE: 删除数据库表"),
    (re.compile(r'\bgit\s+push\s+--force\b'), "git push --force: 强制推送"),
    (re.compile(r'\btruncate\b', re.IGNORECASE), "TRUNCATE: 清空数据库表"),
    (
        re.compile(
            r'\bdelete\s+from\b(?!.*\bwhere\b)',
            re.IGNORECASE | re.DOTALL,
        ),
        "DELETE FROM 缺少 WHERE 子句: 全表删除",
    ),
]

# 安全白名单 —— 这些 rm 命令是安全的
SAFE_PATTERNS: list[re.Pattern] = [
    re.compile(r'\brm\s+-rf\s+/tmp/'),
    re.compile(r'\brm\s+-rf\s+\.git/'),
    re.compile(r'\brm\s+-rf\s+node_modules'),
    re.compile(r'\brm\s+-rf\s+__pycache__'),
    re.compile(r'\brm\s+-rf\s+.+-env'),
    re.compile(r'\brm\s+-rf\s+dist/'),
    re.compile(r'\brm\s+-rf\s+build/'),
    re.compile(r'\brm\s+-rf\s+\.next/'),
]


def _load_input():
    # type: () -> dict | None
    """从 stdin 读取 JSON 输入。"""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        return None


def _get_project_path(data):
    # type: (dict | None) -> str
    """猜测项目路径。"""
    if data and "cwd" in data:
        return data["cwd"]
    # fallback: 用当前目录
    return os.getcwd()


def _ensure_log_dir() -> None:
    """确保日志目录存在。"""
    log_dir = os.path.dirname(BLOCKED_LOG)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


def _append_log(cmd: str, reason: str, project: str) -> None:
    """追加一条阻断记录到日志文件。"""
    _ensure_log_dir()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  command: {cmd}\n"
        f"  project: {project}\n"
        f"{'-' * 60}\n"
    )
    with open(BLOCKED_LOG, "a") as f:
        f.write(entry)


def _get_command_text(data):
    # type: (dict | None) -> str
    """从输入里提取要执行的命令文本。"""
    if data is None:
        return ""
    # Claude Code hook 传入的 tool_use 对象可能在不同版本略有不同
    # 常见的字段：command / input / text
    return (
        data.get("command")
        or data.get("input", {}).get("command", "")
        or data.get("text", "")
        or json.dumps(data, ensure_ascii=False)
    )


def check_safe(cmd):
    # type: (str) -> bool
    """检查命令是否匹配安全白名单。"""
    for pat in SAFE_PATTERNS:
        if pat.search(cmd):
            return True
    return False


def check_dangerous(cmd):
    # type: (str) -> str | None
    """检查命令是否危险。返回 None 表示安全，返回 str 表示原因。"""
    for pat, reason in DANGEROUS_PATTERNS:
        if pat.search(cmd):
            return reason
    return None


def main() -> None:
    data = _load_input()
    cmd = _get_command_text(data)
    project = _get_project_path(data)

    if not cmd.strip():
        # 空命令 —— 放行
        sys.exit(0)

    # 先过白名单
    if check_safe(cmd):
        sys.exit(0)

    # 再查危险模式
    reason = check_dangerous(cmd)
    if reason is not None:
        _append_log(cmd, reason, project)
        message = (
            f"⛔ 危险命令已被 pre-tool-use hook 拦截\n"
            f"原因: {reason}\n"
            f"命令: {cmd[:200]}{'…' if len(cmd) > 200 else ''}\n"
            f"已记录至: {BLOCKED_LOG}\n"
            f"如需执行，请在 ~/.claude/hooks/ 中暂时禁用此 hook。"
        )
        print(message, flush=True)
        # 非零退出码 = 拒绝执行
        sys.exit(1)

    # 安全 —— 放行
    sys.exit(0)


if __name__ == "__main__":
    main()
