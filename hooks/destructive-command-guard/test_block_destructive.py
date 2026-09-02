#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE / "block_destructive.py"


def run_hook(command=None, *, tool_name="Bash", raw=None, home=None):
    env = os.environ.copy()
    if home:
        env["HOME"] = str(home)
    if raw is None:
        raw = json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        })
    return subprocess.run([sys.executable, str(HOOK)], input=raw, text=True,
                          capture_output=True, env=env, check=False)


class GuardTests(unittest.TestCase):
    def assertBlocked(self, command):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_hook(command, home=tmp)
            self.assertEqual(proc.returncode, 0)
            out = json.loads(proc.stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "PreToolUse")
            self.assertEqual(out["permissionDecision"], "deny")
            self.assertTrue(out["permissionDecisionReason"])
            log = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            record = json.loads(log.read_text(encoding="utf-8").strip())
            self.assertEqual(record["command"], command)
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertIn("timestamp", record)
            self.assertIn("reason", record)

    def assertAllowed(self, command, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_hook(command, home=tmp, **kwargs)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_rf(self): self.assertBlocked("rm -rf /tmp/demo")
    def test_blocks_rm_fr(self): self.assertBlocked("rm -fr /tmp/demo")
    def test_blocks_rm_split_flags(self): self.assertBlocked("rm -r -f /tmp/demo")
    def test_blocks_rm_upper_recursive_flag(self): self.assertBlocked("rm -Rf /tmp/demo")
    def test_blocks_rm_long_flags(self): self.assertBlocked("rm --recursive --force /tmp/demo")
    def test_blocks_sudo_rm_rf(self): self.assertBlocked("sudo rm -rf /tmp/demo")
    def test_allows_plain_rm(self): self.assertAllowed("rm file.txt")
    def test_allows_recursive_without_force(self): self.assertAllowed("rm -r build")

    def test_blocks_git_push_force(self): self.assertBlocked("git push --force origin main")
    def test_blocks_git_push_f(self): self.assertBlocked("git push -f origin main")
    def test_blocks_force_with_lease(self): self.assertBlocked("git push --force-with-lease origin main")
    def test_blocks_force_with_lease_value(self): self.assertBlocked("git push --force-with-lease=main origin main")
    def test_blocks_plus_refspec(self): self.assertBlocked("git push origin +main:main")
    def test_allows_normal_git_push(self): self.assertAllowed("git push origin feature")

    def test_blocks_drop_table(self): self.assertBlocked("DROP TABLE users")
    def test_blocks_drop_table_case_insensitive(self): self.assertBlocked("drop table IF EXISTS users")
    def test_blocks_truncate(self): self.assertBlocked("TRUNCATE users")
    def test_blocks_truncate_table(self): self.assertBlocked("truncate table users")
    def test_blocks_delete_without_where(self): self.assertBlocked("DELETE FROM users")
    def test_blocks_delete_without_where_semicolon(self): self.assertBlocked("delete from users;")
    def test_allows_delete_with_where(self): self.assertAllowed("DELETE FROM users WHERE id = 1")
    def test_allows_delete_with_lowercase_where(self): self.assertAllowed("delete from users where id=1")
    def test_allows_echoed_sql_example(self): self.assertAllowed("echo 'DROP TABLE users'")

    def test_allows_safe_command(self): self.assertAllowed("npm test && git status")
    def test_ignores_non_bash_tool(self): self.assertAllowed("rm -rf /tmp/demo", tool_name="Read")
    def test_malformed_json_fails_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_hook(raw="{not-json", home=tmp)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
    def test_empty_command_allowed(self): self.assertAllowed("")
    def test_blocked_log_is_jsonl_for_multiple_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run_hook("rm -rf /tmp/a", home=tmp)
            second = run_hook("git push --force", home=tmp)
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            lines = (Path(tmp) / ".claude" / "hooks" / "blocked.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["command"], "rm -rf /tmp/a")
            self.assertEqual(json.loads(lines[1])["command"], "git push --force")


if __name__ == "__main__":
    unittest.main(verbosity=2)
