# -*- coding: utf-8 -*-
"""test_guard.py — acceptance suite for pre-tool-use-guard (run: python3 test_guard.py)"""
import json, subprocess, sys, os, pathlib

HOOK = pathlib.Path(os.environ.get("GUARD_HOOK", str(pathlib.Path(__file__).parent / "pre_tool_use_guard.py")))

def run_hook(command, cwd="C:\\proj\\demo", tool="Bash"):
    payload = json.dumps({"session_id":"t","tool_name":tool,
                          "tool_input":{"command":command} if tool=="Bash" else {"file_path":command},
                          "cwd":cwd,"hook_event_name":"PreToolUse"})
    p = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]

BLOCK = ["rm -rf /tmp/x","rm -fr /tmp/x","sudo rm -rf /","DROP TABLE users;",
         "drop database prod;","git push --force origin main","git push -f",
         "TRUNCATE TABLE logs;","DELETE FROM users;","delete from sessions"]
ALLOW = ["rm -f /tmp/x.txt","rm -r /tmp/backup","git push origin main",
         "SELECT * FROM users;","DELETE FROM users WHERE id=5;","ls -la",
         "python3 run.py","docker ps"]

def main():
    ok = True
    for c in BLOCK:
        r = run_hook(c)
        if r != "deny":
            ok = False; print("[FAIL] should block: %s -> %s" % (c, r))
    for c in ALLOW:
        r = run_hook(c)
        if r != "allow":
            ok = False; print("[FAIL] should allow: %s -> %s" % (c, r))
    r = run_hook("whatever", tool="Read")
    if r != "allow":
        ok = False; print("[FAIL] non-bash tool -> %s" % r)
    print("ALL_CHECKS_PASS" if ok else "FAILURES")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
