from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block-destructive.py"


def run_hook(command: str, cwd: str = "/tmp/project") -> tuple[int, dict | None, str]:
    payload = {"cwd": cwd, "tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    output = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, output, result.stderr


class DestructiveGuardTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        commands = [
            "rm -rf build",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE TABLE audit_log",
            "DELETE FROM users",
        ]
        for command in commands:
            with self.subTest(command=command):
                code, output, stderr = run_hook(command)
                self.assertEqual(code, 0, stderr)
                self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_normal_commands_and_safe_delete(self) -> None:
        commands = [
            "pwd",
            "ls -la",
            "rm build/output.txt",
            "git push origin main",
            "DELETE FROM users WHERE id = 7",
            "npm test",
        ]
        for command in commands:
            with self.subTest(command=command):
                code, output, stderr = run_hook(command)
                self.assertEqual(code, 0, stderr)
                self.assertIsNone(output)

    def test_logs_every_blocked_command(self) -> None:
        source = __import__("importlib.util").util.spec_from_file_location("guard", HOOK)
        module = __import__("importlib.util").util.module_from_spec(source)
        source.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "hooks" / "blocked.log"
            payload = {"cwd": "/workspace/demo", "tool_input": {"command": "rm -rf dist"}}
            decision = module.process_event(payload, log_path)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["command"], "rm -rf dist")
            self.assertEqual(record["project_path"], "/workspace/demo")
            self.assertIn("recursive", record["reason"])


if __name__ == "__main__":
    unittest.main()
