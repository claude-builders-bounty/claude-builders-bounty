from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "block_dangerous_bash.py"


def run_hook(command: str, home: Path | None = None) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "C:/tmp/project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


class HookTests(unittest.TestCase):
    def test_blocks_rm_rf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            proc = run_hook("rm -rf ./build", home=home)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
            log_file = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_file.exists())
            self.assertIn("rm -rf ./build", log_file.read_text(encoding="utf-8"))

    def test_blocks_force_push_but_not_force_with_lease(self) -> None:
        blocked = run_hook("git push --force origin main")
        self.assertEqual(blocked.returncode, 0)
        self.assertEqual(
            json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

        allowed = run_hook("git push --force-with-lease origin main")
        self.assertEqual(allowed.returncode, 0)
        self.assertEqual(allowed.stdout.strip(), "")

    def test_allows_safe_command(self) -> None:
        proc = run_hook("echo safe")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
