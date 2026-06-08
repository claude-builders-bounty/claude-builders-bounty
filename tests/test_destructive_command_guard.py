from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "destructive-command-guard.py"


spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


def _payload(command: str) -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
    )


def _run_hook(command: str, tmp_path: Path, monkeypatch) -> subprocess.CompletedProcess[str]:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOMEDRIVE", str(tmp_path.drive or "C:"))
    monkeypatch.setenv("HOMEPATH", str(tmp_path).removeprefix(tmp_path.drive))
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=_payload(command),
        text=True,
        capture_output=True,
        check=False,
    )


def test_blocks_rm_rf() -> None:
    assert guard.find_block_reason("rm -rf dist") is not None
    assert guard.find_block_reason("sudo rm -fr /tmp/build") is not None


def test_blocks_git_force_push() -> None:
    assert guard.find_block_reason("git push --force origin main") is not None
    assert guard.find_block_reason("git push --force-with-lease") is not None


def test_blocks_risky_sql_only_in_database_context() -> None:
    assert guard.find_block_reason("psql -c 'DROP TABLE users'") is not None
    assert guard.find_block_reason("mysql -e 'TRUNCATE sessions'") is not None
    assert guard.find_block_reason("sqlite3 app.db 'DELETE FROM users'") is not None
    assert guard.find_block_reason("sqlite3 app.db 'DELETE FROM users WHERE id = 1'") is None
    assert guard.find_block_reason("grep 'DROP TABLE' migration-notes.md") is None


def test_allows_normal_commands() -> None:
    assert guard.find_block_reason("npm test") is None
    assert guard.find_block_reason("git push origin feature") is None
    assert guard.find_block_reason("rm build.log") is None


def test_hook_outputs_deny_json_and_log(tmp_path: Path, monkeypatch) -> None:
    result = _run_hook("git push --force origin main", tmp_path, monkeypatch)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "git push --force" in hook_output["permissionDecisionReason"]

    log_path = tmp_path / ".claude" / "hooks" / "blocked.log"
    log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert log_entry["attempted_command"] == "git push --force origin main"
    assert log_entry["project_path"] == "/tmp/example-project"


def test_hook_silent_for_allowed_command(tmp_path: Path, monkeypatch) -> None:
    result = _run_hook("npm test", tmp_path, monkeypatch)

    assert result.returncode == 0
    assert result.stdout == ""
    assert not (tmp_path / ".claude" / "hooks" / "blocked.log").exists()


def test_installer_quotes_python_and_hook_paths() -> None:
    install_path = ROOT / "install.py"
    install_spec = importlib.util.spec_from_file_location("install", install_path)
    installer = importlib.util.module_from_spec(install_spec)
    assert install_spec.loader is not None
    install_spec.loader.exec_module(installer)

    command = installer._hook_entry()["hooks"][0]["command"]
    assert command.startswith(f'"{sys.executable}" "')
    assert command.endswith('destructive-command-guard.py"')
