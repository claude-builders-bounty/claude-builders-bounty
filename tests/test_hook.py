"""
Comprehensive test suite for dangerous_command_guard.py
Run: python -m pytest tests/test_hook.py -v
"""

import importlib.util
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Load the module under test without installing it ─────────────────────────
HOOK_PATH = Path(__file__).parent.parent / "hooks" / "pre-tool-use" / "dangerous_command_guard.py"
spec = importlib.util.spec_from_file_location("dangerous_command_guard", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

check_command = hook.check_command


# ── Helpers ───────────────────────────────────────────────────────────────────

def should_block(cmd: str) -> bool:
    """Return True if the command matches a dangerous pattern."""
    dangerous, _, _ = check_command(cmd)
    return dangerous


def should_allow(cmd: str) -> bool:
    return not should_block(cmd)


def run_hook(command: str, env: dict | None = None) -> tuple[int, dict | None]:
    """
    Invoke hook.main() with a Bash tool payload, capturing stdout as JSON.
    Returns (exit_code, parsed_json_or_None).
    """
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})

    env_vars = {**os.environ, **(env or {})}
    # Suppress colour output in tests
    env_vars.pop("TERM", None)

    import io
    captured_stdout = io.StringIO()

    with (
        patch("sys.stdin", io.StringIO(payload)),
        patch("sys.stdout", captured_stdout),
        patch.dict(os.environ, env_vars, clear=True),
    ):
        try:
            hook.main()
            exit_code = 0
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 0

    output = captured_stdout.getvalue().strip()
    parsed = json.loads(output) if output else None
    return exit_code, parsed


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Filesystem destruction
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilesystemDestruction:

    def test_rm_rf_slash(self):
        """Classic disk-wiper."""
        assert should_block("rm -rf /")

    def test_rm_rf_dot(self):
        """Deletes current directory."""
        assert should_block("rm -rf .")

    def test_rm_rf_star(self):
        """Deletes everything in cwd."""
        assert should_block("rm -rf *")

    def test_rm_fr_variant(self):
        """-fr flag order variant."""
        assert should_block("rm -fr /tmp/stuff")

    def test_rm_rf_with_sudo(self):
        """Preceded by sudo."""
        assert should_block("sudo rm -rf /home/user")

    def test_rm_recursive_only_allowed(self):
        """Plain -r without -f should not be blocked (recoverable)."""
        assert should_allow("rm -r /tmp/mydir")

    def test_find_delete_flag(self):
        assert should_block("find . -name '*.pyc' -delete")

    def test_find_dash_dash_delete(self):
        assert should_block("find /var/log --delete")

    def test_shred_file(self):
        assert should_block("shred -u secret.txt")

    def test_dd_dev_zero(self):
        assert should_block("dd if=/dev/zero of=/dev/sda bs=1M")

    def test_dd_dev_random(self):
        assert should_block("dd if=/dev/random of=/dev/sdb")

    def test_mkfs_ext4(self):
        assert should_block("mkfs.ext4 /dev/sda1")

    def test_mkfs_generic(self):
        assert should_block("mkfs /dev/nvme0n1")

    def test_write_to_block_device(self):
        assert should_block("cat image.bin > /dev/sda")

    def test_safe_rm_file(self):
        """Removing a single named file is fine."""
        assert should_allow("rm myfile.txt")

    def test_safe_cp_command(self):
        assert should_allow("cp -r src/ dst/")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SQL statements
# ═══════════════════════════════════════════════════════════════════════════════

class TestSQL:

    def test_drop_table(self):
        assert should_block("DROP TABLE users;")

    def test_drop_table_lowercase(self):
        assert should_block("drop table sessions;")

    def test_drop_database(self):
        assert should_block("DROP DATABASE production;")

    def test_drop_schema(self):
        assert should_block("DROP SCHEMA public CASCADE;")

    def test_truncate_table(self):
        assert should_block("TRUNCATE TABLE logs;")

    def test_truncate_no_table_keyword(self):
        assert should_block("TRUNCATE events;")

    def test_delete_without_where(self):
        assert should_block("DELETE FROM orders;")

    def test_delete_without_where_newline(self):
        assert should_block("DELETE FROM orders\n;")

    def test_delete_where_1_equals_1(self):
        """WHERE 1=1 deletes everything — extra dangerous."""
        assert should_block("DELETE FROM orders WHERE 1=1;")

    def test_delete_with_real_where_allowed(self):
        """Legitimate DELETE with a real WHERE clause."""
        assert should_allow("DELETE FROM sessions WHERE user_id = 42;")

    def test_select_star_allowed(self):
        assert should_allow("SELECT * FROM users;")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Git operations
# ═══════════════════════════════════════════════════════════════════════════════

class TestGit:

    def test_git_push_force(self):
        assert should_block("git push origin main --force")

    def test_git_push_f_short(self):
        assert should_block("git push -f origin main")

    def test_git_push_force_with_lease_allowed(self):
        """--force-with-lease is the safe alternative — allow it."""
        assert should_allow("git push --force-with-lease origin main")

    def test_git_reset_hard_head_tilde(self):
        assert should_block("git reset --hard HEAD~1")

    def test_git_reset_hard_head_caret(self):
        assert should_block("git reset --hard HEAD^")

    def test_git_clean_fd(self):
        assert should_block("git clean -fd")

    def test_git_clean_df(self):
        assert should_block("git clean -df")

    def test_git_log_allowed(self):
        assert should_allow("git log --oneline -20")

    def test_git_status_allowed(self):
        assert should_allow("git status")

    def test_git_reset_soft_allowed(self):
        """Soft reset is recoverable."""
        assert should_allow("git reset --soft HEAD~1")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Kubernetes
# ═══════════════════════════════════════════════════════════════════════════════

class TestKubernetes:

    def test_kubectl_delete_namespace(self):
        assert should_block("kubectl delete namespace production")

    def test_kubectl_delete_ns_abbrev(self):
        assert should_block("kubectl delete ns staging")

    def test_kubectl_delete_all_all(self):
        assert should_block("kubectl delete all --all")

    def test_kubectl_delete_pods_all(self):
        assert should_block("kubectl delete pods --all")

    def test_kubectl_delete_all_namespaces(self):
        assert should_block("kubectl delete pods --all --all-namespaces")

    def test_kubectl_get_allowed(self):
        assert should_allow("kubectl get pods -n default")

    def test_kubectl_apply_allowed(self):
        assert should_allow("kubectl apply -f deployment.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. End-to-end hook behaviour
# ═══════════════════════════════════════════════════════════════════════════════

class TestHookEndToEnd:

    def test_block_decision_json(self):
        """Hook outputs {"decision":"block"} for a dangerous command."""
        _, output = run_hook("rm -rf /")
        assert output is not None
        assert output["decision"] == "block"
        assert "reason" in output

    def test_allow_safe_command(self):
        """Hook produces no output (exits 0) for a safe command."""
        exit_code, output = run_hook("echo hello")
        assert exit_code == 0
        assert output is None

    def test_non_bash_tool_ignored(self):
        """Hook ignores non-Bash tool calls."""
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}})
        import io
        captured = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(payload)),
            patch("sys.stdout", captured),
        ):
            try:
                hook.main()
                exit_code = 0
            except SystemExit as exc:
                exit_code = exc.code if isinstance(exc.code, int) else 0
        assert exit_code == 0
        assert captured.getvalue().strip() == ""

    def test_allow_dangerous_override(self, tmp_path):
        """ALLOW_DANGEROUS=1 bypasses the block."""
        with patch.dict(os.environ, {"ALLOW_DANGEROUS": "1", "CLAUDE_PROJECT_DIR": str(tmp_path)}):
            # Re-patch BLOCKED_LOG to a temp file
            with patch.object(hook, "BLOCKED_LOG", tmp_path / "blocked.log"):
                _, output = run_hook("rm -rf /")
        # Should be None (allowed, no JSON block output)
        assert output is None

    def test_dry_run_returns_allow(self):
        """HOOK_DRY_RUN=1 returns allow decision."""
        with patch.dict(os.environ, {"HOOK_DRY_RUN": "1"}):
            _, output = run_hook("rm -rf /")
        assert output is not None
        assert output["decision"] == "allow"
        assert "DRY-RUN" in output["reason"]

    def test_audit_log_written(self, tmp_path):
        """A blocked command is written to the audit log."""
        log_file = tmp_path / "blocked.log"
        with patch.object(hook, "BLOCKED_LOG", log_file):
            with patch.object(hook, "HOOKS_DIR", tmp_path):
                run_hook("rm -rf /")
        assert log_file.exists()
        content = log_file.read_text()
        assert "BLOCKED" in content
        assert "rm -rf /" in content

    def test_audit_log_contains_timestamp(self, tmp_path):
        """Audit log entries include an ISO-8601 timestamp."""
        log_file = tmp_path / "blocked.log"
        with patch.object(hook, "BLOCKED_LOG", log_file):
            with patch.object(hook, "HOOKS_DIR", tmp_path):
                run_hook("DROP TABLE users;")
        content = log_file.read_text()
        # timestamp format: [2026-03-28T...Z]
        import re
        assert re.search(r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\]", content)

    def test_audit_log_override_label(self, tmp_path):
        """ALLOW_DANGEROUS override is logged as OVERRIDE_ALLOWED."""
        log_file = tmp_path / "blocked.log"
        with patch.object(hook, "BLOCKED_LOG", log_file):
            with patch.object(hook, "HOOKS_DIR", tmp_path):
                with patch.dict(os.environ, {"ALLOW_DANGEROUS": "1", "CLAUDE_PROJECT_DIR": str(tmp_path)}):
                    run_hook("rm -rf /")
        content = log_file.read_text()
        assert "OVERRIDE_ALLOWED" in content

    def test_block_reason_mentions_command(self):
        """The block reason references the matched pattern description."""
        _, output = run_hook("DROP TABLE customers;")
        assert output is not None
        assert "DROP" in output["reason"] or "SQL" in output["reason"]

    def test_malformed_json_does_not_crash(self):
        """Malformed JSON stdin causes a graceful exit(0)."""
        import io
        with (
            patch("sys.stdin", io.StringIO("not json")),
            patch("sys.stdout", io.StringIO()),
        ):
            try:
                hook.main()
                exit_code = 0
            except SystemExit as exc:
                exit_code = exc.code if isinstance(exc.code, int) else 0
        assert exit_code == 0
