from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


INSTALL_PATH = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("destructive_bash_installer", INSTALL_PATH)
installer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(installer)


class DestructiveBashInstallerTest(unittest.TestCase):
    def test_install_preserves_existing_hooks_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_dir = root / ".claude"
            hook_dir = claude_dir / "hooks"
            settings_path = claude_dir / "settings.json"
            installed_hook = hook_dir / "destructive_bash_guard.py"
            source_hook = Path(__file__).resolve().parents[1] / "destructive_bash_guard.py"
            hook_command = f"python-test {installed_hook}"

            claude_dir.mkdir(parents=True)
            original_settings = {
                "permissions": {"allow": ["Read"]},
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Read",
                            "hooks": [{"type": "command", "command": "existing-read-hook"}],
                        },
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "existing-bash-hook"}],
                        },
                    ]
                },
            }
            settings_path.write_text(json.dumps(original_settings), encoding="utf-8")

            old_values = self._patch_paths(
                claude_dir,
                hook_dir,
                settings_path,
                installed_hook,
                source_hook,
                hook_command,
            )
            try:
                self.assertEqual(installer.main(), 0)
                self.assertEqual(installer.main(), 0)
            finally:
                self._restore_paths(old_values)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["permissions"], original_settings["permissions"])
            read_group = next(group for group in settings["hooks"]["PreToolUse"] if group["matcher"] == "Read")
            bash_group = next(group for group in settings["hooks"]["PreToolUse"] if group["matcher"] == "Bash")
            self.assertEqual(read_group, original_settings["hooks"]["PreToolUse"][0])
            self.assertIn({"type": "command", "command": "existing-bash-hook"}, bash_group["hooks"])
            self.assertEqual(
                sum(hook.get("command") == hook_command for hook in bash_group["hooks"]),
                1,
            )
            self.assertEqual(installed_hook.read_text(encoding="utf-8"), source_hook.read_text(encoding="utf-8"))

            backup = settings_path.with_suffix(".json.bak")
            self.assertTrue(backup.exists())
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8")), original_settings)

    def test_invalid_settings_json_fails_without_replacing_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_dir = root / ".claude"
            hook_dir = claude_dir / "hooks"
            settings_path = claude_dir / "settings.json"
            installed_hook = hook_dir / "destructive_bash_guard.py"
            source_hook = Path(__file__).resolve().parents[1] / "destructive_bash_guard.py"
            hook_command = f"python-test {installed_hook}"

            claude_dir.mkdir(parents=True)
            settings_path.write_text("{not valid json", encoding="utf-8")
            backup = settings_path.with_suffix(".json.bak")
            backup.write_text('{"original": true}', encoding="utf-8")

            old_values = self._patch_paths(
                claude_dir,
                hook_dir,
                settings_path,
                installed_hook,
                source_hook,
                hook_command,
            )
            try:
                with self.assertRaises(SystemExit):
                    installer.main()
            finally:
                self._restore_paths(old_values)

            self.assertEqual(backup.read_text(encoding="utf-8"), '{"original": true}')

    @staticmethod
    def _patch_paths(
        claude_dir: Path,
        hook_dir: Path,
        settings_path: Path,
        installed_hook: Path,
        source_hook: Path,
        hook_command: str,
    ) -> dict[str, object]:
        names = {
            "CLAUDE_DIR": claude_dir,
            "HOOK_DIR": hook_dir,
            "SETTINGS_PATH": settings_path,
            "INSTALLED_HOOK": installed_hook,
            "SOURCE_HOOK": source_hook,
            "HOOK_COMMAND": hook_command,
        }
        old_values = {name: getattr(installer, name) for name in names}
        for name, value in names.items():
            setattr(installer, name, value)
        return old_values

    @staticmethod
    def _restore_paths(old_values: dict[str, object]) -> None:
        for name, value in old_values.items():
            setattr(installer, name, value)


if __name__ == "__main__":
    unittest.main()
