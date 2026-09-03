#!/usr/bin/env python3
"""
Unit tests for the install.py installer script.
"""

import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

INSTALL_SCRIPT = Path(__file__).resolve().parent.parent / "install.py"


class TestInstaller(unittest.TestCase):
    """Tests for installation script behavior and configuration generation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_claude = Path(self.temp_dir.name) / ".claude"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_installer(self, args: list = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(self.target_claude)]
        if args:
            cmd.extend(args)
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True
        )

    def test_clean_installation(self):
        proc = self.run_installer()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[SUCCESS]", proc.stdout)

        # Verify hook file exists
        target_hook = self.target_claude / "hooks" / "block_destructive.py"
        self.assertTrue(target_hook.exists())
        self.assertGreater(target_hook.stat().st_size, 0)

        # Verify settings.json exists and is valid JSON
        settings_file = self.target_claude / "settings.json"
        self.assertTrue(settings_file.exists())
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pre_tool_hooks = data.get("hooks", {}).get("PreToolUse", [])
        self.assertTrue(len(pre_tool_hooks) > 0)
        bash_entry = pre_tool_hooks[0]
        self.assertEqual(bash_entry.get("matcher"), "Bash")
        commands = [h.get("command") for h in bash_entry.get("hooks", [])]
        self.assertTrue(any("block_destructive.py" in cmd for cmd in commands))

    def test_preserves_existing_settings(self):
        self.target_claude.mkdir(parents=True, exist_ok=True)
        settings_file = self.target_claude / "settings.json"
        initial_data = {
            "customSetting": True,
            "hooks": {
                "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo post"}]}]
            }
        }
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        proc = self.run_installer()
        self.assertEqual(proc.returncode, 0)

        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertTrue(data.get("customSetting"))
        self.assertIn("PostToolUse", data.get("hooks", {}))
        self.assertIn("PreToolUse", data.get("hooks", {}))

    def test_installer_is_idempotent(self):
        self.run_installer()
        proc = self.run_installer()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("already configured", proc.stdout)

        settings_file = self.target_claude / "settings.json"
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pre_tool_hooks = data.get("hooks", {}).get("PreToolUse", [])
        # Only 1 entry for Bash
        bash_entries = [e for e in pre_tool_hooks if e.get("matcher") == "Bash"]
        self.assertEqual(len(bash_entries), 1)

    def test_dry_run_does_not_modify_filesystem(self):
        proc = self.run_installer(["--dry-run"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[MODE: DRY RUN", proc.stdout)
        self.assertFalse(self.target_claude.exists())


if __name__ == "__main__":
    unittest.main()
