import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import destructive_guard as guard


class DetectionTests(unittest.TestCase):
    def assert_blocked(self, command: str, contains: str):
        finding = guard.inspect_command(command)
        self.assertTrue(finding.blocked, command)
        self.assertIn(contains, finding.reason)

    def assert_allowed(self, command: str):
        finding = guard.inspect_command(command)
        self.assertFalse(finding.blocked, f"unexpected block for: {command} -> {finding.reason}")

    def test_blocks_rm_rf_variants_but_not_safe_rm(self):
        self.assert_blocked("rm -rf .next/cache", "rm")
        self.assert_blocked("rm -fr -- /tmp/build", "rm")
        self.assert_blocked("rm --recursive --force ./dist", "rm")
        self.assert_allowed("rm -f ./tmp-file")
        self.assert_allowed("echo 'rm -rf /' >> docs/safety.md")

    def test_blocks_force_push_variants(self):
        self.assert_blocked("git push --force origin main", "force push")
        self.assert_blocked("git push -f", "force push")
        self.assert_blocked("git push --force-with-lease", "force push")
        self.assert_allowed("git push origin feature/destructive-guard")

    def test_blocks_dangerous_sql_in_db_clients_and_raw_sql(self):
        self.assert_blocked("sqlite3 app.db 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("psql \"$DATABASE_URL\" -c \"TRUNCATE audit_log\"", "TRUNCATE")
        self.assert_blocked("DELETE FROM sessions", "DELETE FROM")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < datetime(\"now\")'")

    def test_sql_detection_avoids_documentation_search_false_positives(self):
        self.assert_allowed("grep -R \"DROP TABLE\" docs/")
        self.assert_allowed("printf 'DELETE FROM users' >> examples.sql")
        self.assert_allowed("python - <<'PY'\nprint('TRUNCATE')\nPY")


class HookIOTests(unittest.TestCase):
    def test_extracts_bash_command_from_claude_payload(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": "/repo"}
        self.assertEqual(guard.extract_command(payload), "git status")

    def test_non_bash_tools_are_allowed(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}, "cwd": "/repo"}
        decision = guard.evaluate_payload(payload)
        self.assertFalse(decision.blocked)

    def test_blocked_cli_writes_log_and_structured_deny(self):
        script = ROOT / "destructive_guard.py"
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "blocked.log"
            env = os.environ.copy()
            env["CLAUDE_HOOK_LOG"] = str(log_path)
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ."},
                "cwd": "/tmp/project-a",
            }
            proc = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            output = json.loads(proc.stdout)
            specific = output["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "PreToolUse")
            self.assertEqual(specific["permissionDecision"], "deny")
            self.assertIn("rm", specific["permissionDecisionReason"])
            log_text = log_path.read_text()
            self.assertIn("rm -rf .", log_text)
            self.assertIn("/tmp/project-a", log_text)

    def test_allowed_cli_is_silent_success(self):
        script = ROOT / "destructive_guard.py"
        payload = {"tool_name": "Bash", "tool_input": {"command": "npm test"}, "cwd": "/tmp/project-b"}
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_installer_merges_settings_without_clobbering_existing_hooks(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "settings.json"
            settings.write_text(json.dumps({"hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": []}]}}))
            guard.install_settings(settings_path=settings, hook_path=Path("/x/destructive_guard.py"))
            data = json.loads(settings.read_text())
            self.assertIn("PostToolUse", data["hooks"])
            pre = data["hooks"]["PreToolUse"]
            self.assertEqual(pre[0]["matcher"], "Bash")
            self.assertIn("destructive_guard.py", pre[0]["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
