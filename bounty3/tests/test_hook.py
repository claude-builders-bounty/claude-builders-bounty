from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive_commands.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(
    command: str,
    home: Path,
    *,
    tool_name: str = "Bash",
    cwd: str = "C:/synthetic/project",
) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="destructive-hook-") as temp:
        home = Path(temp) / "home"
        home.mkdir()
        log_path = home / ".claude" / "hooks" / "blocked.log"

        blocked = [
            "rm -rf",
            "rm -rf /tmp/build",
            "rm -fr ./build",
            "sudo rm --recursive --force ./data",
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "sudo git push --force origin main",
            "sqlite3 app.db \"DROP TABLE users\"",
            "sqlite3 app.db \"TRUNCATE TABLE events\"",
            "sqlite3 app.db \"DELETE FROM users\"",
        ]
        for command in blocked:
            result = invoke(command, home)
            require(result.returncode == 0, f"hook process failed for {command}")
            require(result.stdout.strip(), f"no decision for blocked command: {command}")
            decision = json.loads(result.stdout)
            specific = decision["hookSpecificOutput"]
            require(specific["hookEventName"] == "PreToolUse", "wrong event name")
            require(specific["permissionDecision"] == "deny", f"not denied: {command}")
            require("Blocked destructive command" in specific["permissionDecisionReason"], "unclear reason")

        powershell_result = invoke("rm -rf C:/temp/build", home, tool_name="PowerShell")
        require(powershell_result.returncode == 0, "PowerShell payload failed")
        require(json.loads(powershell_result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny", "PowerShell payload was not denied")

        allowed = [
            "rm ./build.log",
            "git push origin main",
            "git status --short",
            "python -m pytest",
            "sqlite3 app.db \"DELETE FROM users WHERE id = 1\"",
            "sqlite3 app.db \"DELETE FROM users WHERE id = 1; DELETE FROM audit WHERE id = 2\"",
            "echo \"ordinary command\"",
        ]
        for command in allowed:
            result = invoke(command, home)
            require(result.returncode == 0, f"hook process failed for allowed command: {command}")
            require(result.stdout == "", f"normal command interfered: {command!r}")

        # A matching string from a different tool must not be acted on by this
        # Bash/PowerShell hook group.
        result = invoke("rm -rf /tmp/build", home, tool_name="Read")
        require(result.stdout == "", "non-shell tool was blocked")

        # Bad input is non-blocking and does not create a fake log entry.
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        malformed = subprocess.run(
            [sys.executable, str(HOOK)],
            input="{not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        require(malformed.returncode == 0, "malformed payload caused a hook failure")
        require(malformed.stdout == "", "malformed payload produced a decision")

        # Logging failure must fail closed rather than letting a destructive
        # call through. A file is used as HOME so .claude cannot be created.
        unusable_home = Path(temp) / "home-file"
        unusable_home.write_text("not a directory", encoding="utf-8")
        failed_log = invoke("rm -rf /tmp/build", unusable_home)
        require(failed_log.returncode == 2, "logging failure did not block")
        require("audit log could not be written" in failed_log.stderr, "logging failure was unclear")

        require(log_path.exists(), "blocked.log was not created")
        records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        require(len(records) == len(blocked) + 1, "unexpected number of log records")
        for record, command in zip(records, blocked):
            require(record["attempted_command"] == command, "logged command mismatch")
            require(record["project_path"] == "C:/synthetic/project", "project path mismatch")
            require(record["reasons"], "missing match reason")
            datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))

    print("test_hook.py: PASS (blocking, exceptions, logs, tool filtering, malformed input, and non-interference)")


if __name__ == "__main__":
    main()
