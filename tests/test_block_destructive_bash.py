import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, home: Path):
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp/example-project",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={"HOME": str(home)},
        check=False,
    )


class BlockDestructiveBashHookTest(unittest.TestCase):
    def test_allows_normal_bash_commands(self):
        with TemporaryDirectory() as home:
            home_path = Path(home)
            result = run_hook("git status --short", home_path)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((home_path / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_rf_and_logs_attempt(self):
        with TemporaryDirectory() as home:
            home_path = Path(home)
            result = run_hook("rm -rf build", home_path)

            self.assertEqual(result.returncode, 2)
            self.assertIn("permissionDecision", result.stdout)
            self.assertIn("rm -rf", result.stderr)

            log_path = home_path / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_path.read_text().splitlines()[0])
            self.assertEqual(record["command"], "rm -rf build")
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertEqual(record["reason"], "recursive forced remove (rm -rf)")

    def test_blocks_equivalent_rm_recursive_force_forms(self):
        for command in ("rm -fr build", "rm -r -f build", "rm --recursive --force build"):
            with self.subTest(command=command), TemporaryDirectory() as home:
                result = run_hook(command, Path(home))
                self.assertEqual(result.returncode, 2)

    def test_blocks_sql_keywords_case_insensitively(self):
        blocked_commands = [
            "psql -c 'DROP TABLE users'",
            "psql -c 'truncate audit_log'",
            "mysql -e 'DELETE FROM users'",
        ]

        for command in blocked_commands:
            with self.subTest(command=command), TemporaryDirectory() as home:
                result = run_hook(command, Path(home))
                self.assertEqual(result.returncode, 2)

    def test_allows_delete_from_with_where_clause(self):
        with TemporaryDirectory() as home:
            command = "psql -c 'DELETE FROM sessions WHERE expires_at < now()'"
            result = run_hook(command, Path(home))
            self.assertEqual(result.returncode, 0)

    def test_blocks_git_push_force_but_allows_normal_push(self):
        with TemporaryDirectory() as home:
            home_path = Path(home)
            forced = run_hook("git push origin main --force", home_path)
            normal = run_hook("git push origin main", home_path)

            self.assertEqual(forced.returncode, 2)
            self.assertEqual(normal.returncode, 0)


if __name__ == "__main__":
    unittest.main()
