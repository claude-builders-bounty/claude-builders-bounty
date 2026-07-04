from __future__ import annotations

import importlib.util
import pathlib
import sys


SCRIPT_PATH = pathlib.Path(__file__).with_name("block_destructive_bash.py")
spec = importlib.util.spec_from_file_location("block_destructive_bash", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["block_destructive_bash"] = module
spec.loader.exec_module(module)


def assert_blocked(command: str) -> None:
    result = module.evaluate_command(command)
    assert result.blocked, command


def assert_allowed(command: str) -> None:
    result = module.evaluate_command(command)
    assert not result.blocked, command


def test_blocked_patterns() -> None:
    assert_blocked("rm -rf dist")
    assert_blocked("DROP TABLE users")
    assert_blocked("git push --force origin main")
    assert_blocked("git push -f origin main")
    assert_blocked("TRUNCATE TABLE sessions")
    assert_blocked("DELETE FROM users")


def test_allowed_patterns() -> None:
    assert_allowed("ls -la")
    assert_allowed("rm -r build")
    assert_allowed("git push origin main")
    assert_allowed("SELECT * FROM users")
    assert_allowed("DELETE FROM users WHERE id = 123")


if __name__ == "__main__":
    test_blocked_patterns()
    test_allowed_patterns()
    print("ok")
