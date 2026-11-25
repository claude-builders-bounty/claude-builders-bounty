"""
自动化测试 - Pre-tool-use bash 安全钩
题目: [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands
ID: github-bash-guard
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple

HOOK_SCRIPT = Path(__file__).resolve().parent / "solution.py"


def run_hook(command: str) -> Tuple[int, str, str]:
    """运行 hook 并返回 (returncode, stdout, stderr)"""
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps({"tool": "bash", "command": command}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_blocks_destructive_rm_rf():
    rc, out, err = run_hook("rm -rf /tmp/important")
    assert rc != 0, f"应拦截 rm -rf，实际 rc={rc}"
    data = json.loads(out)
    assert data["blocked"] is True


def test_blocks_shutdown():
    rc, out, err = run_hook("shutdown -h now")
    assert rc != 0
    data = json.loads(out)
    assert data["blocked"] is True


def test_blocks_mkfs():
    rc, out, err = run_hook("mkfs.ext4 /dev/sdb")
    assert rc != 0
    data = json.loads(out)
    assert data["blocked"] is True


def test_allows_safe_command():
    rc, out, err = run_hook("ls -la /tmp")
    assert rc == 0, f"安全命令应放行，实际 rc={rc}, stderr={err}"
    data = json.loads(out)
    assert data["blocked"] is False


def test_blocks_dd():
    rc, out, err = run_hook("dd if=/dev/zero of=/dev/sda")
    assert rc != 0
    data = json.loads(out)
    assert data["blocked"] is True


if __name__ == "__main__":
    import unittest

    unittest.main()
