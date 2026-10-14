#!/usr/bin/env python3
"""Test-suite for block_destructive.py.

Feeds every line of corpus_dangerous.txt and corpus_safe.txt to the hook as a
synthetic Claude Code PreToolUse payload (realistic stdin JSON, cwd set),
then checks:

  dangerous -> exit 0, stdout is the documented deny JSON
               (hookSpecificOutput.permissionDecision == "deny" with a reason)
  safe      -> exit 0, stdout completely empty (no output pollution)

Finally it verifies ~/.claude/hooks/blocked.log (redirected to a temp file via
BLOCK_DESTRUCTIVE_LOG) holds exactly one entry per dangerous command, each
with a timestamp, the project cwd, and the attempted command.

Usage:  python3 tests/run_tests.py
Prints one PASS/FAIL line per case plus a summary; exit code 0 iff all green.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE.parent / "block_destructive.py"
TEST_CWD = "/tmp/testproject"


def load_corpus(name):
    lines = []
    for raw in (HERE / name).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def run_hook(command, log_path, tool_name="Bash", raw_stdin=None):
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/test-transcript.jsonl",
        "cwd": TEST_CWD,
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "tool_use_id": "toolu_test",
    }
    env = dict(os.environ, BLOCK_DESTRUCTIVE_LOG=str(log_path))
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw_stdin if raw_stdin is not None else json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=30,
    )


def main():
    dangerous = load_corpus("corpus_dangerous.txt")
    safe = load_corpus("corpus_safe.txt")
    passed = failed = 0

    def report(ok, label, detail=""):
        nonlocal passed, failed
        if ok:
            passed += 1
            print("PASS  %s" % label)
        else:
            failed += 1
            print("FAIL  %s  %s" % (label, detail))

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "blocked.log"

        print("== Dangerous corpus: %d commands, all must BLOCK ==" % len(dangerous))
        for cmd in dangerous:
            proc = run_hook(cmd, log_path)
            ok, detail = True, ""
            if proc.returncode != 0:
                ok, detail = False, "(exit %d)" % proc.returncode
            else:
                try:
                    out = json.loads(proc.stdout)
                    hso = out["hookSpecificOutput"]
                    assert hso["hookEventName"] == "PreToolUse"
                    assert hso["permissionDecision"] == "deny"
                    assert hso["permissionDecisionReason"].strip()
                except Exception as exc:  # noqa: BLE001
                    ok, detail = False, "(bad deny JSON: %s)" % exc
            report(ok, "BLOCK  %s" % cmd, detail)

        print("\n== Safe corpus: %d commands, all must PASS untouched ==" % len(safe))
        for cmd in safe:
            proc = run_hook(cmd, log_path)
            ok = proc.returncode == 0 and proc.stdout.strip() == ""
            report(ok, "ALLOW  %s" % cmd,
                   "" if ok else "(exit %d, stdout=%r)" % (proc.returncode, proc.stdout[:80]))

        print("\n== Robustness: hook must never break a session ==")
        proc = run_hook("", log_path, raw_stdin="this is not json")
        report(proc.returncode == 0 and proc.stdout == "",
               "ALLOW  malformed stdin (fail-open)")
        proc = run_hook("rm -rf /", log_path, tool_name="Edit")
        report(proc.returncode == 0 and proc.stdout == "",
               "ALLOW  non-Bash tool ignored")
        proc = run_hook("", log_path)
        report(proc.returncode == 0 and proc.stdout == "",
               "ALLOW  empty command ignored")

        print("\n== blocked.log verification ==")
        lines = []
        if log_path.exists():
            lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        report(len(lines) == len(dangerous),
               "log has exactly %d entries (one per blocked command)" % len(dangerous),
               "(got %d)" % len(lines))
        for cmd in dangerous:
            hit = [l for l in lines
                   if cmd.replace("\n", "\\n") in l and ("cwd=" + TEST_CWD) in l
                   and l.startswith("[") and "]" in l]
            report(bool(hit), "log entry w/ timestamp+cwd for: %s" % cmd)

    print("\n== SUMMARY: %d passed, %d failed ==" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
