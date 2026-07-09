#!/usr/bin/env python3
"""Deterministic acceptance check for the block-destructive-bash hook.

Exit 0 iff every acceptance criterion holds:
  - required files exist,
  - each required destructive pattern is BLOCKED (exit 2),
  - normal commands are ALLOWED (exit 0) — the hook does not interfere,
  - blocked attempts are logged with timestamp, command, and project path.

Run from the repo root:  python hooks/validate_hook.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
HOOK = REPO / ".claude" / "hooks" / "block_destructive_bash.py"

REQUIRED = [
    ".claude/hooks/block_destructive_bash.py",
    "hooks/README.md",
    "hooks/install.sh",
]

BLOCK = [
    "rm -rf /tmp/x",
    "rm -fr build",
    "rm --recursive --force node_modules",
    "sudo rm -rf --no-preserve-root /",
    "git push --force origin main",
    "git push -f",
    "psql -c 'DROP TABLE users'",
    "mysql -e 'TRUNCATE logs;'",
    "sqlite3 app.db 'DELETE FROM sessions'",
]
ALLOW = [
    "ls -la",
    "rm file.txt",
    "rm -r build_dir",                       # recursive only, no force
    "git push origin main",
    "git push --force-with-lease origin feat",  # safe force is not blocked
    "psql -c 'DELETE FROM sessions WHERE id = 1'",  # bounded delete is fine
    "echo 'rm -rf is only a string'",        # not an actual rm invocation start... (see note)
]


def fail(msg: str) -> int:
    print(f"VALIDATION_FAILED: {msg}")
    return 1


def main() -> int:
    for rel in REQUIRED:
        p = REPO / rel
        if not p.is_file() or p.stat().st_size < 20:
            return fail(f"missing/empty deliverable: {rel}")

    # Scratch OUTSIDE the repo (so it is never a "changed path") and cleaned up.
    scratch = Path(__file__).resolve().parents[2] / f"_hookval_{uuid.uuid4().hex[:8]}"
    logdir = scratch / "logs"
    try:
        logdir.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "SystemRoot": os.environ.get("SystemRoot", ""),
            "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
            "CLAUDE_HOOKS_DIR": str(logdir),
        }

        def run(cmd: str) -> int:
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(scratch)})
            proc = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                                  text=True, env=env, timeout=30)
            return proc.returncode

        for cmd in BLOCK:
            if run(cmd) != 2:
                return fail(f"destructive command was NOT blocked: {cmd!r}")
        for cmd in ALLOW:
            rc = run(cmd)
            if rc != 0:
                return fail(f"normal command was blocked (interference): {cmd!r} rc={rc}")

        other = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}})
        if subprocess.run([sys.executable, str(HOOK)], input=other, capture_output=True, text=True,
                          env=env, timeout=30).returncode != 0:
            return fail("hook interfered with a non-Bash tool call")

        log = logdir / "blocked.log"
        if not log.is_file():
            return fail("blocked.log was not created")
        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) < len(BLOCK):
            return fail(f"blocked.log has {len(lines)} entries, expected >= {len(BLOCK)}")
        first = lines[0].split("\t")
        if len(first) != 3 or "T" not in first[0]:
            return fail(f"log line not 'timestamp<TAB>project<TAB>command': {lines[0]!r}")

        print(f"VALIDATION_OK: {len(BLOCK)} destructive patterns blocked, {len(ALLOW)} normal commands "
              f"allowed, {len(lines)} attempts logged with timestamp/project/command.")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
