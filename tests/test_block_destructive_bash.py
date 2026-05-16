import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks" / "destructive-bash-guard" / "block_destructive_bash.py"


def run_hook(command, tmpdir, tool_name="Bash"):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "cwd": "/tmp/project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["CLAUDE_HOOK_LOG"] = str(pathlib.Path(tmpdir) / "blocked.log")
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class BlockDestructiveBashTests(unittest.TestCase):
    def test_allows_normal_bash_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook("git status --short", tmpdir)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_ignores_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook("rm -rf /tmp/example", tmpdir, tool_name="Read")

        self.assertEqual(result.returncode, 0)

    def test_blocks_recursive_forced_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook("rm -rf build", tmpdir)
            log = pathlib.Path(tmpdir) / "blocked.log"

            self.assertEqual(result.returncode, 2)
            self.assertIn("Recursive forced deletion", result.stderr)
            self.assertTrue(log.exists())

    def test_blocks_drop_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook('psql -c "DROP TABLE users"', tmpdir)

        self.assertEqual(result.returncode, 2)
        self.assertIn("DROP TABLE", result.stderr)

    def test_blocks_truncate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook('psql -c "TRUNCATE TABLE audit_log"', tmpdir)

        self.assertEqual(result.returncode, 2)
        self.assertIn("TRUNCATE", result.stderr)

    def test_blocks_force_push(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook("git push --force origin main", tmpdir)

        self.assertEqual(result.returncode, 2)
        self.assertIn("Force-pushing", result.stderr)

    def test_blocks_delete_from_without_where(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook('psql -c "DELETE FROM users"', tmpdir)

        self.assertEqual(result.returncode, 2)
        self.assertIn("without WHERE", result.stderr)

    def test_allows_delete_from_with_where(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook('psql -c "DELETE FROM users WHERE id = 1"', tmpdir)

        self.assertEqual(result.returncode, 0)

    def test_log_contains_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_hook("rm -fr build", tmpdir)
            log_line = (pathlib.Path(tmpdir) / "blocked.log").read_text(encoding="utf-8").strip()

        entry = json.loads(log_line)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["attempted_command"], "rm -fr build")
        self.assertEqual(entry["project_path"], "/tmp/project")
        self.assertIn("reason", entry)


if __name__ == "__main__":
    unittest.main()

