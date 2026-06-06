#!/usr/bin/env python3
import subprocess
import json
import sys
import os

HOOK = os.path.join(os.path.dirname(__file__), "pre-tool-use.py")


def run_hook(payload):
    if isinstance(payload, dict):
        data = json.dumps(payload)
    else:
        data = payload
    return subprocess.run(
        [sys.executable, HOOK],
        input=data,
        text=True,
        capture_output=True,
    )


def assert_blocked(payload, label):
    result = run_hook(payload)
    assert result.returncode != 0, f"Expected blocked: {label}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert "SECURITY CHECK FAILED" in result.stderr, f"Expected warning message for {label}"


def assert_allowed(payload, label):
    result = run_hook(payload)
    assert result.returncode == 0, f"Expected allowed: {label}\nstdout={result.stdout}\nstderr={result.stderr}"


def main():
    # Dangerous commands should be blocked
    assert_blocked({"tool": "bash", "arguments": {"command": "rm -rf ./dist"}}, "rm -rf")
    assert_blocked({"tool": "bash", "input": {"command": "DROP TABLE users;"}}, "DROP TABLE")
    assert_blocked({"tool": "bash", "input": {"command": "git push --force origin main"}}, "git push --force")
    assert_blocked({"tool": "bash", "input": {"command": "git push -f origin main"}}, "git push -f")
    assert_blocked({"tool": "bash", "input": {"command": "TRUNCATE sessions;"}}, "TRUNCATE")
    assert_blocked({"tool": "bash", "input": {"command": "DELETE FROM users;"}}, "DELETE FROM without WHERE")

    # Plain text stdin should also be blocked
    assert_blocked("rm -rf /tmp/something", "plain text rm -rf")

    # Safe commands should pass
    assert_allowed({"tool": "bash", "arguments": {"command": "ls -la"}}, "ls")
    assert_allowed({"tool": "bash", "arguments": {"command": "git status"}}, "git status")
    assert_allowed({"tool": "bash", "arguments": {"command": "DELETE FROM users WHERE id = 1;"}}, "DELETE with WHERE")
    assert_allowed({"tool": "bash", "arguments": {"command": "rm -r ./dist"}}, "rm -r without force")

    print("All security hook tests passed.")


if __name__ == "__main__":
    main()
