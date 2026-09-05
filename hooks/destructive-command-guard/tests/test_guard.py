"""
Verification Test Suite for Claude Code Pre-Tool-Use Destructive Command Guard.
Ensures 100% compliance with Opire Bounty #3 acceptance criteria.
"""

import os
import json
import pytest
from pathlib import Path
import sys

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from pre_tool_use_bash_guard import DestructiveCommandGuard, run_guard


@pytest.fixture
def temp_log(tmp_path):
    return tmp_path / "blocked.log"


class TestDestructiveCommandGuard:

    @pytest.mark.parametrize(
        "cmd,expected_rule",
        [
            ("rm -rf /", "RM_RF"),
            ("rm -rf node_modules", "RM_RF"),
            ("rm -fr dist", "RM_RF"),
            ("rm -r -f build", "RM_RF"),
            ("rm --recursive --force /tmp/test", "RM_RF"),
            ("DROP TABLE users;", "DROP_TABLE"),
            ("drop table customers", "DROP_TABLE"),
            ("git push --force origin main", "GIT_PUSH_FORCE"),
            ("git push -f upstream master", "GIT_PUSH_FORCE"),
            ("git push origin feature --force-with-lease", "GIT_PUSH_FORCE"),
            ("TRUNCATE TABLE logs;", "TRUNCATE"),
            ("truncate audit_events", "TRUNCATE"),
            ("DELETE FROM accounts;", "DELETE_WITHOUT_WHERE"),
            ("DELETE FROM users", "DELETE_WITHOUT_WHERE"),
        ],
    )
    def test_blocks_destructive_commands(self, temp_log, cmd, expected_rule):
        guard = DestructiveCommandGuard(log_path=temp_log)
        is_blocked, rule_name, reason = guard.evaluate_command(cmd)

        assert is_blocked is True, f"Command '{cmd}' should have been blocked!"
        assert rule_name == expected_rule
        assert len(reason) > 0

    @pytest.mark.parametrize(
        "cmd",
        [
            "ls -la",
            "git status",
            "git push origin feat/cool-feature",
            "git pull --rebase",
            "rm specific_file.txt",
            "pytest tests/",
            "npm run build",
            "DELETE FROM users WHERE id = 101;",
            "delete from accounts where balance <= 0",
            "SELECT * FROM users WHERE deleted = false;",
            "cargo test --all",
        ],
    )
    def test_allows_benign_commands(self, temp_log, cmd):
        guard = DestructiveCommandGuard(log_path=temp_log)
        is_blocked, rule_name, reason = guard.evaluate_command(cmd)

        assert is_blocked is False, f"Benign command '{cmd}' was incorrectly blocked ({rule_name})!"
        assert rule_name == "CLEAN"

    def test_audit_log_format(self, temp_log):
        guard = DestructiveCommandGuard(log_path=temp_log)
        test_cmd = "rm -rf /var/www"
        project_dir = "/workspace/my-app"

        is_blocked, rule, _ = guard.evaluate_command(test_cmd)
        assert is_blocked is True
        guard.log_blocked(test_cmd, project_dir, rule)

        assert temp_log.exists()
        lines = temp_log.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["rule"] == "RM_RF"
        assert record["attempted_command"] == test_cmd
        assert record["project_path"] == project_dir
        assert "timestamp" in record

    def test_run_guard_exit_codes(self, temp_log):
        # 1. Payload with destructive command -> returns 1
        destructive_payload = {
            "tool": "Bash",
            "input": {"command": "git push --force origin main"}
        }
        code = run_guard(destructive_payload, log_override=temp_log)
        assert code == 1

        # 2. Payload with safe command -> returns 0
        safe_payload = {
            "tool": "Bash",
            "input": {"command": "git status"}
        }
        code = run_guard(safe_payload, log_override=temp_log)
        assert code == 0
