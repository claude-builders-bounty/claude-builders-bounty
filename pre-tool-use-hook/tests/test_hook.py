"""Tests for the pre-tool-use safety hook."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "pre-tool-use-safety.py"


def _run_hook(payload: dict) -> dict | None:
    """Run the hook with a JSON payload on stdin. Returns parsed output or None."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    if stdout:
        return json.loads(stdout)
    return None


def _make_payload(command: str, tool_name: str = "Bash", cwd: str = "/tmp/test") -> dict:
    return {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": cwd,
    }


# ---------------------------------------------------------------------------
# Should BLOCK
# ---------------------------------------------------------------------------

class TestShouldBlock:
    def test_rm_rf(self):
        result = _run_hook(_make_payload("rm -rf /some/path"))
        assert result is not None
        assert result["decision"] == "block"
        assert "rm -rf" in result["reason"].lower()

    def test_rm_rf_flag_order(self):
        result = _run_hook(_make_payload("rm -fr /some/path"))
        assert result is not None
        assert result["decision"] == "block"

    def test_rm_rf_with_other_flags(self):
        result = _run_hook(_make_payload("rm -rfv /tmp/something"))
        assert result is not None
        assert result["decision"] == "block"

    def test_drop_table(self):
        result = _run_hook(_make_payload("psql -c 'DROP TABLE users;'"))
        assert result is not None
        assert result["decision"] == "block"
        assert "DROP TABLE" in result["reason"]

    def test_drop_table_case_insensitive(self):
        result = _run_hook(_make_payload("psql -c 'drop table users;'"))
        assert result is not None
        assert result["decision"] == "block"

    def test_truncate(self):
        result = _run_hook(_make_payload("psql -c 'TRUNCATE logs;'"))
        assert result is not None
        assert result["decision"] == "block"

    def test_delete_from_without_where(self):
        result = _run_hook(_make_payload("psql -c 'DELETE FROM sessions;'"))
        assert result is not None
        assert result["decision"] == "block"

    def test_git_push_force(self):
        result = _run_hook(_make_payload("git push --force origin main"))
        assert result is not None
        assert result["decision"] == "block"
        assert "force" in result["reason"].lower()

    def test_git_push_f_short(self):
        result = _run_hook(_make_payload("git push -f origin main"))
        assert result is not None
        assert result["decision"] == "block"

    def test_response_contains_command(self):
        cmd = "rm -rf /critical/path"
        result = _run_hook(_make_payload(cmd))
        assert result is not None
        assert cmd in result["reason"]


# ---------------------------------------------------------------------------
# Should ALLOW
# ---------------------------------------------------------------------------

class TestShouldAllow:
    def test_safe_ls(self):
        result = _run_hook(_make_payload("ls -la"))
        assert result is None

    def test_safe_rm(self):
        result = _run_hook(_make_payload("rm file.txt"))
        assert result is None

    def test_rm_r_without_f(self):
        # rm -r is risky but NOT in our block list
        result = _run_hook(_make_payload("rm -r ./build"))
        assert result is None

    def test_delete_from_with_where(self):
        result = _run_hook(_make_payload("psql -c 'DELETE FROM sessions WHERE created_at < now() - INTERVAL 30'"))
        assert result is None

    def test_git_push_normal(self):
        result = _run_hook(_make_payload("git push origin main"))
        assert result is None

    def test_git_push_force_with_lease(self):
        # force-with-lease is safer — not blocked
        result = _run_hook(_make_payload("git push --force-with-lease origin feature"))
        assert result is None

    def test_select_from(self):
        result = _run_hook(_make_payload("psql -c 'SELECT * FROM users WHERE id=1'"))
        assert result is None

    def test_echo_command(self):
        result = _run_hook(_make_payload("echo hello world"))
        assert result is None

    def test_non_bash_tool_skipped(self):
        payload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/etc/passwd"},
            "cwd": "/tmp",
        }
        result = _run_hook(payload)
        assert result is None

    def test_empty_command(self):
        result = _run_hook(_make_payload(""))
        assert result is None

    def test_malformed_input(self):
        # Should not crash — just exit 0
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json at all",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class TestLogging:
    def test_blocked_command_is_logged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / ".claude" / "hooks"
            log_file = log_dir / "blocked.log"

            # Patch HOME env so log goes to tmpdir
            env = {**os.environ, "HOME": tmpdir}
            subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(_make_payload("rm -rf /danger")),
                capture_output=True,
                text=True,
                env=env,
            )

            assert log_file.exists(), "blocked.log was not created"
            content = log_file.read_text()
            assert "BLOCKED" in content
            assert "rm -rf /danger" in content

    def test_allowed_command_not_logged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / ".claude" / "hooks"
            log_file = log_dir / "blocked.log"

            env = {**os.environ, "HOME": tmpdir}
            subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(_make_payload("ls -la")),
                capture_output=True,
                text=True,
                env=env,
            )

            assert not log_file.exists(), "blocked.log should not exist for safe commands"
