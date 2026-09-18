import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import destructive_command_hook as hook


class DetectionTests(unittest.TestCase):
    def test_required_destructive_patterns(self):
        cases = {
            "rm -rf ./build": "rm-rf",
            "rm -r -f ./build": "rm-rf",
            "git push origin main --force": "git-push-force",
            'psql -c "DROP TABLE users"': "drop-table",
            "TRUNCATE TABLE audit": "truncate",
            "DELETE FROM users": "delete-without-where",
            "DELETE FROM users WHERE id = 1": None,
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                finding = hook.find_destructive_command(command)
                self.assertEqual(None if finding is None else finding.rule, expected)

    def test_compounds_and_powershell(self):
        self.assertEqual(hook.find_destructive_command("echo ok && rm -rf x").rule, "rm-rf")
        self.assertEqual(hook.find_destructive_command("Remove-Item x -Recurse -Force").rule, "powershell-recursive-delete")
        self.assertEqual(hook.find_destructive_command("git push origin main").rule if hook.find_destructive_command("git push origin main") else None, None)

    def test_quoted_separators_are_not_treated_as_compound_commands(self):
        self.assertEqual(hook._split_shell_segments('echo "rm -rf | ejemplo; sigue"'), ['echo "rm -rf | ejemplo; sigue"'])
        self.assertEqual(hook._split_shell_segments("Write-Output 'DELETE FROM users; WHERE id = 1'"), ["Write-Output 'DELETE FROM users; WHERE id = 1'"])
        self.assertIsNone(hook.find_destructive_command('echo "rm -rf | ejemplo"'))
        self.assertIsNone(hook.find_destructive_command('Write-Output "DELETE FROM users"'))
        self.assertEqual(hook.find_destructive_command('echo "literal | texto" && rm -rf fixture').rule, "rm-rf")
        self.assertEqual(hook.find_destructive_command("printf 'literal; texto' ; git push -f origin main").rule, "git-push-force")

    def test_normal_commands_and_quoted_examples_are_not_blocked(self):
        for command in ["echo 'rm -rf /'", "printf 'DROP TABLE users'", "git status", "rm notes.txt", "SELECT * FROM users"]:
            with self.subTest(command=command):
                self.assertIsNone(hook.find_destructive_command(command))


class HookTests(unittest.TestCase):
    def test_block_logs_and_returns_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "blocked.log"
            event = {"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users"}, "cwd": "C:/project"}
            out, err = io.StringIO(), io.StringIO()
            with patch("sys.stdin", io.StringIO(json.dumps(event))), patch.dict("os.environ", {"DESTRUCTIVE_HOOK_LOG": str(log)}):
                with redirect_stdout(out), redirect_stderr(err):
                    result = hook.main([])
            self.assertEqual(result, 2)
            record = json.loads(log.read_text(encoding="utf-8"))
            self.assertEqual(record["command"], "DELETE FROM users")
            self.assertEqual(record["project_path"], "C:/project")
            self.assertIn("BLOCKED", err.getvalue())
            self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_safe_event_is_allowed(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
        with patch("sys.stdin", io.StringIO(json.dumps(event))):
            self.assertEqual(hook.main([]), 0)


if __name__ == "__main__":
    unittest.main()
