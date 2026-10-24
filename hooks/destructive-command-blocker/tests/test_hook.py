#!/usr/bin/env python3
"""
Comprehensive Test Suite for Claude Code Destructive Command Interceptor Hook
Validates all acceptance criteria:
1. Blocks rm -rf variants
2. Blocks DROP TABLE
3. Blocks git push --force variants
4. Blocks TRUNCATE
5. Blocks DELETE FROM without WHERE
6. Allows safe commands (including DELETE FROM with WHERE)
7. Validates blocked.log audit output
8. Tests both JSON stdin and raw command invocations
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"
if not HOOK_PATH.exists():
    HOOK_PATH = Path(__file__).resolve().parent / "pre-tool-use.py"

def run_hook_with_payload(payload=None, args=None, env=None):
    """Executes the hook subprocess and returns (returncode, stdout, stderr)."""
    custom_env = os.environ.copy()
    if env:
        custom_env.update(env)
    
    cmd = [sys.executable, str(HOOK_PATH)]
    if args:
        cmd.extend(args)

    stdin_data = None
    if payload is not None:
        if isinstance(payload, (dict, list)):
            stdin_data = json.dumps(payload)
        else:
            stdin_data = str(payload)

    proc = subprocess.run(
        cmd,
        input=stdin_data,
        text=True,
        capture_output=True,
        env=custom_env
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── Test Suite ────────────────────────────────────────────────────────────────

class TestDestructiveCommandBlocker:

    @pytest.mark.parametrize("cmd", [
        "rm -rf /",
        "rm -rf node_modules",
        "rm -fr ./dist",
        "rm -r -f build/",
        "rm -f -r tmp",
        "rm --recursive --force cache/",
        "rm -R -f logs"
    ])
    def test_blocks_rm_rf_variants(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1, f"Failed to block: {cmd}"
        assert "rm -rf" in stderr
        assert "Destructive Bash Command Intercepted" in stderr

    @pytest.mark.parametrize("cmd", [
        "DROP TABLE users;",
        "drop table accounts",
        "DROP TABLE IF EXISTS orders CASCADE;"
    ])
    def test_blocks_drop_table(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1, f"Failed to block: {cmd}"
        assert "DROP TABLE" in stderr

    @pytest.mark.parametrize("cmd", [
        "git push --force origin main",
        "git push -f",
        "git push origin +feat-branch",
        "git push --force-with-lease origin main"
    ])
    def test_blocks_git_force_push(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1, f"Failed to block: {cmd}"
        assert "git push --force" in stderr

    @pytest.mark.parametrize("cmd", [
        "TRUNCATE TABLE sessions;",
        "truncate audit_logs",
        "TRUNCATE users CASCADE"
    ])
    def test_blocks_truncate(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1, f"Failed to block: {cmd}"
        assert "TRUNCATE" in stderr

    @pytest.mark.parametrize("cmd", [
        "DELETE FROM users;",
        "delete from accounts",
        "DELETE FROM sessions"
    ])
    def test_blocks_delete_without_where(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1, f"Failed to block: {cmd}"
        assert "DELETE FROM without WHERE" in stderr

    @pytest.mark.parametrize("cmd", [
        "DELETE FROM users WHERE id = 42;",
        "delete from accounts where balance = 0",
        "DELETE FROM sessions WHERE expires_at < NOW();",
        "rm single_file.txt",
        "rm -r safe_dir", # recursive without force is not rm -rf
        "git push origin main",
        "git status",
        "ls -la",
        "SELECT * FROM users;",
        "pytest -v",
        "npm run build"
    ])
    def test_allows_safe_commands(self, cmd):
        payload = {"tool": "Bash", "input": {"command": cmd}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 0, f"False positive block on safe command: {cmd}\nStderr: {stderr}"

    def test_ignores_non_bash_tools(self):
        # Non-bash tool calls like Read, Edit, Glob should pass immediately
        payload = {"tool": "Read", "input": {"path": "/tmp/rm -rf"}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 0

    def test_positional_cli_invocation(self):
        ret, stdout, stderr = run_hook_with_payload(args=["rm", "-rf", "/tmp"])
        assert ret == 1
        assert "rm -rf" in stderr

    def test_audit_log_written(self):
        log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
        initial_len = len(log_file.read_text(encoding="utf-8")) if log_file.exists() else 0
        
        payload = {"tool": "Bash", "input": {"command": "DROP TABLE test_log;"}}
        ret, stdout, stderr = run_hook_with_payload(payload)
        assert ret == 1

        assert log_file.exists()
        current_content = log_file.read_text(encoding="utf-8")
        assert len(current_content) > initial_len
        assert "DROP TABLE test_log;" in current_content
