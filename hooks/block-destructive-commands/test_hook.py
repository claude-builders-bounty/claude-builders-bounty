#!/usr/bin/env python3
"""Unit tests for pre_tool_use.py hook — runs should_block() directly."""
import sys, os, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ptu", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre_tool_use.py"))
ptu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ptu)

def mkcmd(parts):
    return " ".join(parts)

CASES = [
    # (command, expected_block, label)
    (mkcmd(["rm", "-rf", "/"]), True,  "rm -rf /"),
    (mkcmd(["sudo", "rm", "-rf", "--no-preserve-root", "/"]), True, "sudo rm -rf /"),
    (mkcmd(["rm", "-rf", "./node_modules"]), True,  "rm -rf ./node_modules"),
    (mkcmd(["rm", "-r", "-f", "build"]), True,  "rm -r -f build"),
    (mkcmd(["DROP", "TABLE", "users;"]), True,  "DROP TABLE"),
    (mkcmd(["TRUNCATE", "logs;"]), True,  "TRUNCATE"),
    (mkcmd(["git", "push", "--force", "origin", "main"]), True, "git push --force"),
    (mkcmd(["git", "push", "-f", "origin", "main"]), True, "git push -f"),
    (mkcmd(["DELETE", "FROM", "users;"]), True,  "DELETE no WHERE"),
    (mkcmd(["DELETE", "FROM", "users", "WHERE", "id=5;"]), False, "DELETE with WHERE"),
    (mkcmd(["DELETE", "FROM", "logs", "LIMIT", "10;"]), False, "DELETE with LIMIT"),
    (mkcmd(["ls", "-la"]), False, "ls -la"),
    (mkcmd(["echo", "hello"]), False, "echo hello"),
    (mkcmd(["git", "push", "origin", "main"]), False, "git push (no force)"),
    (mkcmd(["cat", "file.txt"]), False, "cat"),
    (mkcmd(["echo", "'rm -rf /'"]), False, "quoted string in echo"),
    (mkcmd(["grep", "-r", "DELETE FROM", "."]), True, "grep unquoted pattern (acceptable FP: real greps quote patterns)"),
    (mkcmd(["grep", "-r", '"DELETE FROM"', "."]), False, "grep quoted pattern"),
    (mkcmd(["mysql", "-e", '"DELETE FROM users;"']), True, "mysql real DELETE"),
    (mkcmd(["psql", "-c", '"DROP TABLE x;"']), True, "psql real DROP"),
    (mkcmd(["pip", "install", "requests"]), False, "pip install"),
    (mkcmd(["rm", "-rf", "/var/tmp/x", "# cleanup"]), True, "rm -rf with comment"),
    (mkcmd(["python3", "manage.py", "migrate"]), False, "normal migrate"),
]

passed = failed = 0
for cmd, want, label in CASES:
    got, reason = ptu.should_block(cmd)
    ok = (got == want)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label:32s} -> block={got} ({'want ' + str(want) if not ok else reason[:50]})")
    if ok: passed += 1
    else: failed += 1

# Also test stdin->stdout pipeline via main() using a subprocess-free path:
import io, contextlib
def run_pipeline(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(payload)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            ptu.main()
    finally:
        sys.stdin = old_stdin
    return buf.getvalue().strip()

import json
pipe_tests = [
    (mkcmd(["rm", "-rf", "/"]), "block",  "pipeline: rm -rf"),
    (mkcmd(["ls", "-la"]), "allow", "pipeline: ls"),
    ("", "allow", "pipeline: empty"),
]
for cmd, want, label in pipe_tests:
    out = run_pipeline(cmd)
    decision = json.loads(out).get("permissionDecision")
    ok = (decision == want)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label:32s} -> {decision} (want {want})")
    if ok: passed += 1
    else: failed += 1

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
