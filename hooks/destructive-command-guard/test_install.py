from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


INSTALLER = Path(__file__).with_name("install.py")


class InstallerTests(unittest.TestCase):
    def run_installer(self, home: str) -> subprocess.CompletedProcess[str]:
        environment = {**os.environ, "HOME": home, "USERPROFILE": home}
        return subprocess.run(
            [sys.executable, str(INSTALLER)],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )

    def test_preserves_settings_and_installs_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            settings_path = Path(home) / ".claude/settings.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps(
                    {
                        "theme": "dark",
                        "hooks": {
                            "PostToolUse": [{"matcher": "Write", "hooks": []}],
                            "PreToolUse": [{"matcher": "Read", "hooks": []}],
                        },
                    }
                ),
                encoding="utf-8",
            )

            first = self.run_installer(home)
            second = self.run_installer(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["theme"], "dark")
            self.assertEqual(len(settings["hooks"]["PostToolUse"]), 1)
            guards = [
                item
                for item in settings["hooks"]["PreToolUse"]
                if item.get("matcher") == "Bash"
            ]
            self.assertEqual(len(guards), 1)
            self.assertEqual(
                guards[0]["hooks"][0]["args"][0].split("/")[-1],
                "destructive_command_guard.py",
            )
            installed = Path(guards[0]["hooks"][0]["args"][0])
            self.assertTrue(installed.is_file())
            self.assertEqual(installed.stat().st_mode & 0o777, 0o700)

    def test_invalid_settings_are_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            settings_path = Path(home) / ".claude/settings.json"
            settings_path.parent.mkdir(parents=True)
            original = "{ invalid"
            settings_path.write_text(original, encoding="utf-8")

            result = self.run_installer(home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without replacing settings", result.stderr)
            self.assertEqual(settings_path.read_text(encoding="utf-8"), original)
            self.assertFalse((settings_path.parent / "hooks").exists())

    def test_different_existing_guard_file_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            hooks = Path(home) / ".claude/hooks"
            hooks.mkdir(parents=True)
            script = hooks / "destructive_command_guard.py"
            script.write_text("keep this file", encoding="utf-8")

            result = self.run_installer(home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to replace different file contents", result.stderr)
            self.assertEqual(script.read_text(encoding="utf-8"), "keep this file")
            self.assertFalse((hooks.parent / "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
