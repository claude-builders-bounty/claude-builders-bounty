import json, subprocess, sys
from pathlib import Path
HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre_tool_use_safe_bash.py"

def run(cmd, tmp_path):
    payload={"tool_input":{"command":cmd},"cwd":str(tmp_path)}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True)

def test_allows_normal_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    r=run("echo hello && ls -la", tmp_path)
    assert r.returncode == 0

def test_blocks_rm_rf_and_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    r=run("rm -rf /tmp/demo", tmp_path)
    assert r.returncode == 2
    assert "Blocked dangerous bash command" in r.stderr
    log=tmp_path/".claude"/"hooks"/"blocked.log"
    assert log.exists()
    assert "rm -rf" in log.read_text()

def test_blocks_delete_without_where(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert run("psql -c 'DELETE FROM users;'", tmp_path).returncode == 2
    assert run("psql -c 'DELETE FROM users WHERE id=1;'", tmp_path).returncode == 0
