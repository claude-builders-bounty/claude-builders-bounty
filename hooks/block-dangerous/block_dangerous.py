#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive shell commands.

Wire it up in ~/.claude/settings.json:

    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_dangerous.py"}]
          }
        ]
      }
    }

The hook reads the tool call as JSON on stdin and either stays silent (allow)
or prints a PreToolUse decision that denies the call with a reason.

Exit code 0 always: the decision travels in the JSON payload, so a crash in the
hook cannot silently allow a destructive command *and* cannot break the session.
Every deny is appended to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ.get("CLAUDE_HOOK_LOG", Path.home() / ".claude" / "hooks" / "blocked.log"))

# --- patterns -------------------------------------------------------------

GIT_FORCE = re.compile(
    r"git\s+push\b[^\n;|&]*(?:--force(?![\w-])|(?<![\w-])-f(?![\w-]))",
    re.IGNORECASE,
)
DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE = re.compile(r"\btruncate\s+(?:table\s+)?[\w\"'`\[\].]+", re.IGNORECASE)
DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)
# rm 调用：命令分隔符之后出现的 rm
RM_CALL = re.compile(r"(?:^|[;&|]{1,2}|\$\(|`)\s*(?:sudo\s+)?rm\s+([^\n;|&]*)", re.IGNORECASE)


def _rm_is_recursive_force(args: str) -> bool:
    """`rm` 参数里同时出现递归和强制才算危险（-rf / -fr / -r -f / --recursive --force）。"""
    words = re.split(r"\s+", args.strip())
    flags = ""
    recursive = force = False
    for w in words:
        if not w or not w.startswith("-"):
            continue
        if w.startswith("--"):
            low = w.lower()
            if low == "--recursive":
                recursive = True
            if low == "--force":
                force = True
            continue
        flags += w[1:]
    if "r" in flags or "R" in flags:
        recursive = True
    if "f" in flags:
        force = True
    return recursive and force


# 这些命令只是在“念”文本（echo、grep、git commit -m 等），里面的 SQL 字样不是真的执行
TEXT_ONLY_COMMANDS = {
    "echo", "printf", "logger", "cat", "less", "more", "head", "tail",
    "grep", "rg", "ag", "sed", "awk", "diff", "man", "help",
}


def _first_word(statement: str) -> str:
    """取一条语句的第一个词（跳过 sudo / VAR=x 这类前缀）。"""
    for token in statement.strip().split():
        if token == "sudo" or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token):
            continue
        return token.lower().lstrip("(")
    return ""


def check_command(command: str) -> str | None:
    """返回拦截原因；None 表示放行。"""
    # 按语句切分，避免一条 SELECT ... WHERE 掩护另一条 DELETE
    statements = [s for s in re.split(r"(?:;|\n|\|\||&&)", command) if s.strip()]

    if GIT_FORCE.search(command):
        return "`git push --force` 会覆盖远端历史，别人已拉取的工作可能被冲掉。"

    for stmt in statements:
        head = _first_word(stmt)
        if head in TEXT_ONLY_COMMANDS:
            continue  # 只是打印/搜索文本，不执行
        if head == "git":
            continue  # git 只看上面的 --force，不当 SQL 看
        if DROP_TABLE.search(stmt):
            return "`DROP TABLE` 会直接删表，数据不可恢复。"
        if TRUNCATE.search(stmt):
            return "`TRUNCATE` 会清空整张表，且无法回滚到行级。"
        if DELETE_FROM.search(stmt) and not WHERE.search(stmt):
            return "`DELETE FROM` 没有 `WHERE` 子句，等于清空全表。"
        for match in RM_CALL.finditer(stmt):
            if _rm_is_recursive_force(match.group(1)):
                return "`rm -rf` 递归强制删除，路径一旦写错就救不回来。"
    return None


def log_block(project_path: str, command: str, reason: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        one_line = " ".join(command.split())[:500]
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp}\t{project_path}\t{reason}\t{one_line}\n")
    except OSError:
        # 日志写不进去也不能放行，下面照旧 deny
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0  # 读不懂就当没这回事，交给 Claude Code 自己的权限流程

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not command.strip():
        return 0

    reason = check_command(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or tool_input.get("cwd") or Path.cwd())
    log_block(project_path, command, reason)

    message = (
        f"命令被危险操作钩子拦截：{reason}\n"
        "如果确实要做，请把动作拆小（先 `ls`/`git log` 确认目标），"
        "或明确告诉用户这一步会删/改什么、影响哪个目录，由用户手动执行。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
