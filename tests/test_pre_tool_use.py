#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import tempfile

# Import hook logic dynamically
hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "pre-tool-use.py"
sys.path.insert(0, str(hook_path.parent))
import importlib.util
spec = importlib.util.spec_from_file_location("pre_tool_use", str(hook_path))
assert spec is not None and spec.loader is not None
pre_tool_use = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pre_tool_use)

def test_is_destructive():
    test_cases = [
        ("ls -la /home/user", False),
        ("git status", False),
        ("echo 'hello world'", False),
        ("SELECT * FROM users WHERE id=1;", False),
        ("DELETE FROM users WHERE id = 42;", False),
        ("rm -rf /", True),
        ("rm -rf ./build", True),
        ("rm -fr dist/", True),
        ("git push --force origin main", True),
        ("git push -u origin main -f", True),
        ("DROP TABLE production_users;", True),
        ("drop table if exists accounts", True),
        ("TRUNCATE logs;", True),
        ("DELETE FROM orders;", True),
        ("delete from cache", True),
    ]
    for cmd, expected_blocked in test_cases:
        blocked, reason = pre_tool_use.is_destructive(cmd)
        assert blocked == expected_blocked, f"Failed on command: '{cmd}' (expected {expected_blocked}, got {blocked}: {reason})"

def test_extract_command_json():
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /important_data"}
    })
    extracted = pre_tool_use.extract_command(payload)
    assert extracted == "rm -rf /important_data"

def test_log_blocked_attempt():
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "blocked.log"
        pre_tool_use.log_blocked_attempt("rm -rf /", "rm -rf", log_file=log_file)
        assert log_file.exists()
        content = log_file.read_text()
        assert "BLOCKED (rm -rf): rm -rf /" in content

def test_extract_command_raw_string():
    extracted = pre_tool_use.extract_command("git push --force")
    assert extracted == "git push --force"

if __name__ == "__main__":
    test_is_destructive()
    test_extract_command_json()
    test_log_blocked_attempt()
    test_extract_command_raw_string()
    print("PYTHON SELF-CHECK PASSED: 18/18 unit checks (destructive bash/SQL interception + JSON parsing + log verified).")