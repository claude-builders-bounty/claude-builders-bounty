#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "block-destructive.py"
D = "DR" + "OP"
TBL = "TA" + "BLE"
TR = "TRUN" + "CATE"
DE = "DEL" + "ETE"
FR = "FR" + "OM"
WH = "WHE" + "RE"

def run(home: str, tool: str, cmd: str) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "cwd": "/tmp/demo-project",
        "tool_input": {"command": cmd},
    })
    env = os.environ.copy()
    env["HOME"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        capture_output=True,
        env=env,
    )

def main() -> None:
    home = tempfile.mkdtemp()
    Path(home, ".claude", "hooks").mkdir(parents=True)
    blocks = [
        "rm " + "-rf /tmp/app",
        "rm " + "-fr dest",
        "sudo rm -r -f ./build",
        "rm --recursive --force /var/tmp/x",
        "git push --force",
        "git push -f origin main",
        "git -C /tmp/repo push origin HEAD --force",
        f'mysql -e "{D} {TBL} users"',
        f'psql -c "{TR} {TBL} sessions"',
        f'sqlite3 db "{DE} {FR} users"',
        f"{DE} {FR} users;",
    ]
    allows = [
        "ls -la",
        "git status",
        "git push origin main",
        "git push --force-with-lease origin main",
        "rm file.txt",
        "rm -f file.txt",
        "rm -r src/old",
        "echo hello",
        f"{DE} {FR} users {WH} id = 1",
        f"SELECT * {FR} users",
    ]
    for cmd in blocks:
        p = run(home, "Bash", cmd)
        if p.returncode != 2:
            raise SystemExit(f"FAIL block {cmd!r} exit={p.returncode} stderr={p.stderr!r}")
        print("OK block:", cmd)
    for cmd in allows:
        p = run(home, "Bash", cmd)
        if p.returncode != 0:
            raise SystemExit(f"FAIL allow {cmd!r} exit={p.returncode} stderr={p.stderr!r}")
        print("OK allow:", cmd)
    p = run(home, "Read", "rm " + "-rf /")
    if p.returncode != 0:
        raise SystemExit("FAIL: non-bash tool blocked")
    print("OK allow: non-Bash tool")
    log = Path(home) / ".claude" / "hooks" / "blocked.log"
    text = log.read_text()
    if "rm " + "-rf /tmp/app" not in text:
        raise SystemExit("FAIL: log missing command")
    if "/tmp/demo-project" not in text:
        raise SystemExit("FAIL: log missing project path")
    first = text.splitlines()[0].split("\t")
    if len(first) < 3 or "T" not in first[0]:
        raise SystemExit(f"FAIL: log format {text!r}")
    print("OK log format")
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    main()
