#!/usr/bin/env python3
"""Smoke tests for the destructive Bash guard."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = load_module("block_destructive_bash", Path(__file__).with_name("block_destructive_bash.py"))
installer = load_module("install_destructive_bash_guard", Path(__file__).with_name("install.py"))


BLOCKED = [
    "rm -rf build",
    "rm -fr build",
    "rm --recursive --force build",
    "rm -r --force build",
    "rm --force -r build",
    'bash -c "rm -rf build"',
    "psql -c 'DROP TABLE users'",
    "sqlite3 app.db 'TRUNCATE TABLE audit_log'",
    "git push --force origin main",
    "git push -f origin main",
    "git push --force-with-lease origin main",
    "sqlite3 app.db 'DELETE FROM users'",
    "sqlite3 app.db 'DELETE FROM users' | grep where",
    "sqlite3 app.db 'DELETE FROM users -- where'",
    "sqlite3 app.db 'DELETE FROM users /* where */'",
    "sqlite3 app.db \"DELETE FROM users 'where'\"",
    "sqlite3 app.db \"DELETE FROM users \"\"where\"\"\"",
]

ALLOWED = [
    "git status",
    "rm -r build",
    "truncate -s 0 file.log",
    "truncate audit_log",
    "python manage.py migrate",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
    "sqlite3 app.db \"DELETE FROM users WHERE note = 'where'\"",
    "git push origin main",
]


def test_blocked_commands() -> None:
    for command in BLOCKED:
        assert guard.block_reason(command), f"expected blocked: {command}"


def test_allowed_commands() -> None:
    for command in ALLOWED:
        assert guard.block_reason(command) is None, f"expected allowed: {command}"


def test_redacts_secrets() -> None:
    redacted = guard.redact_command("curl -H 'Bearer sk-test' https://user:pass@example.com API_KEY=abc123")
    assert "sk-test" not in redacted
    assert "abc123" not in redacted
    assert "user:pass" not in redacted


def test_installer_rejects_unexpected_settings_shapes() -> None:
    for invalid in (
        {"hooks": []},
        {"hooks": {"PreToolUse": {}}},
        {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": {}}]}},
    ):
        try:
            installer.merge_hook(invalid, 'python3 "/tmp/block_destructive_bash.py"')
        except SystemExit:
            pass
        else:
            raise AssertionError(f"expected invalid settings shape to fail: {invalid}")


def test_installer_uses_current_python() -> None:
    destination = Path("/tmp/block_destructive_bash.py")
    command = installer.hook_command(destination)
    assert command == installer.command_string([sys.executable, str(destination)])


def test_installer_rejects_symlink_destination() -> None:
    if os.name == "nt" or not hasattr(os, "symlink"):
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        source = tmp_path / "source.py"
        source.write_text("print('hook')\n", encoding="utf-8")
        target = tmp_path / "target.py"
        destination = tmp_path / "block_destructive_bash.py"
        os.symlink(target, destination)

        try:
            installer.install_hook_file(source, destination)
        except SystemExit as exc:
            assert "symlink" in str(exc).lower()
        else:
            raise AssertionError("expected symlink destination to be rejected")


def test_write_settings_atomic_preserves_valid_json() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        installer.write_settings_atomic(settings_path, {"hooks": {"PreToolUse": []}})
        assert '"PreToolUse": []' in settings_path.read_text(encoding="utf-8")


def test_log_block_rejects_symlink() -> None:
    if os.name == "nt" or not hasattr(os, "symlink"):
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "blocked.log"
        target_path = Path(tmpdir) / "target.log"
        os.symlink(target_path, log_path)

        original_log_file_path = guard.log_file_path
        guard.log_file_path = lambda: log_path
        try:
            try:
                guard.log_block("rm -rf build", "/tmp/project", "blocked")
            except SystemExit as exc:
                assert "symlink" in str(exc).lower()
            else:
                raise AssertionError("expected symlink log path to be rejected")
        finally:
            guard.log_file_path = original_log_file_path


def test_log_block_rejects_path_swap_after_open() -> None:
    if os.name == "nt":
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "blocked.log"
        original_log_file_path = guard.log_file_path
        original_open = guard.os.open

        def swapping_open(path, flags, mode=0o777):
            fd = original_open(path, flags, mode)
            if Path(path) == log_path:
                log_path.unlink()
                log_path.write_text("replacement\n", encoding="utf-8")
            return fd

        guard.log_file_path = lambda: log_path
        guard.os.open = swapping_open
        try:
            try:
                guard.log_block("rm -rf build", "/tmp/project", "blocked")
            except SystemExit as exc:
                assert "path changed" in str(exc).lower()
            else:
                raise AssertionError("expected swapped log path to be rejected")
        finally:
            guard.os.open = original_open
            guard.log_file_path = original_log_file_path


def main() -> int:
    test_blocked_commands()
    test_allowed_commands()
    test_redacts_secrets()
    test_installer_rejects_unexpected_settings_shapes()
    test_installer_uses_current_python()
    test_installer_rejects_symlink_destination()
    test_write_settings_atomic_preserves_valid_json()
    test_log_block_rejects_symlink()
    test_log_block_rejects_path_swap_after_open()
    print("All destructive Bash guard checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
