#!/usr/bin/env python3
"""block_dangerous.py 的测试：跑 `python3 tests/test_hook.py`。

每个用例喂一段 Claude Code 会送进来的 JSON，断言 hook 的 stdout/日志。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = [
    HERE.parent / "block_dangerous.py",          # hooks/block-dangerous/tests/ 布局
    HERE.parent / "hooks" / "block_dangerous.py",  # 仓库根/tests/ 布局
    HERE.parent.parent / "hooks" / "block_dangerous.py",
]
HOOK = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])


def run_hook(command: str, log_path: Path, cwd: str = "/work/demo") -> tuple[int, str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    env = dict(
        os.environ,
        CLAUDE_HOOK_LOG=str(log_path),
        PYTHONIOENCODING="utf-8",
        PYTHONUTF8="1",
    )
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        env=env,
        cwd=str(HOOK.parent),
    )
    return proc.returncode, proc.stdout.decode()


def denied(stdout: str) -> tuple[bool, str]:
    if not stdout.strip():
        return False, ""
    data = json.loads(stdout)
    out = data.get("hookSpecificOutput", {})
    return out.get("permissionDecision") == "deny", out.get("permissionDecisionReason", "")


BLOCKED = [
    "rm -rf /tmp/build",
    "rm -fr node_modules",
    "rm -r -f ./dist",
    "sudo rm --recursive --force /var/data",
    "cd app && rm -rf .git",
    "psql -c 'DROP TABLE users;'",
    "mysql -e 'drop table if exists orders'",
    "psql -c 'TRUNCATE TABLE audit_log'",
    "psql -c 'DELETE FROM sessions'",
    "psql -c 'delete from a; delete from b where id = 1'",
    "git push --force origin main",
    "git push -f",
    "git push origin main --force",
]

ALLOWED = [
    "ls -la",
    "rm build/out.o",
    "rm -r build",
    "rm -f stale.log",
    "git push origin main",
    "git push --force-with-lease origin main",
    "git status",
    "psql -c 'DELETE FROM sessions WHERE id = 3'",
    "psql -c 'SELECT * FROM users WHERE id = 1'",
    "grep -rn 'rm -rf' docs/",
    "echo 'DROP TABLE is dangerous'",
    "git commit -m 'fix: clarify DROP TABLE guardrails'",
    "cat docs/drop-table-policy.md",
    "npm test",
]


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "blocked.log"

        for cmd in BLOCKED:
            code, out = run_hook(cmd, log)
            ok, reason = denied(out)
            if code != 0 or not ok:
                failures.append(f"应拦截却没拦: {cmd!r} (exit={code}, out={out[:120]!r})")
            elif not reason:
                failures.append(f"拦了但没给理由: {cmd!r}")

        for cmd in ALLOWED:
            code, out = run_hook(cmd, log)
            ok, _ = denied(out)
            if code != 0 or ok:
                failures.append(f"不该拦却拦了: {cmd!r} (exit={code}, out={out[:120]!r})")

        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        if len(lines) != len(BLOCKED):
            failures.append(f"日志条数 {len(lines)} != 拦截次数 {len(BLOCKED)}")
        for line in lines:
            parts = line.split("\t")
            if len(parts) != 4:
                failures.append(f"日志格式不对: {line!r}")
                break
            if parts[1] != "/work/demo":
                failures.append(f"项目路径没记对: {parts[1]!r}")
                break

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        return 1

    print(f"OK — {len(BLOCKED)} blocked, {len(ALLOWED)} allowed, log lines={len(BLOCKED)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
