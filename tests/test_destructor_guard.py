#!/usr/bin/env python3
"""End-to-end tests for destructor_guard.py: feed hook JSON via stdin, assert exit codes.

Blocked commands must exit 2 (tool call cancelled) and allowed commands must exit 0.
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "destructor_guard.py")

# Root = "/" is assembled from parts so this file itself is harmless to run.
ROOT = "/"

SHOULD_BLOCK = [
    "rm -rf " + ROOT,
    "rm -rf ~",
    "rm -fr " + ROOT,
    "rm --recursive --force " + ROOT,
    "git push --force origin main",
    "git push -f origin master",
    "git push --force-with-lease origin main",
    "git push --mirror --force origin",
    'psql -c "DROP TABLE users"',
    "mysql -e 'drop database prod'",
    "TRUNCATE TABLE logs",
    "mkfs.ext4 /dev/sda1",
    "dd if=/dev/zero of=/dev/sda bs=1M",
    "echo x > /dev/sda",
    "chmod -R 777 " + ROOT,
    ":(){ :|:& };:",
    "sudo shutdown -h now",
]

SHOULD_ALLOW = [
    "rm -rf ./build",
    "rm -rf dist node_modules",
    "rm ./tmp.txt",
    "git push --force origin feature-branch",
    "git push origin main",
    "git push origin main:main",
    "ls -la /tmp",
    "npm install",
    "chmod 644 config.yaml",
    "git reset --hard HEAD~1",
]


def run_hook(cmd):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["DESTRUCTOR_GUARD_LOG"] = tempfile.mktemp()
    return subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )


def main():
    failures = 0
    for cmd in SHOULD_BLOCK:
        r = run_hook(cmd)
        ok = r.returncode == 2
        if not ok:
            failures += 1
        print("%-4s (exit %d) %-45s %s" % ("PASS" if ok else "FAIL", r.returncode, cmd, (r.stderr or "").strip()[:90]))
    for cmd in SHOULD_ALLOW:
        r = run_hook(cmd)
        ok = r.returncode == 0
        if not ok:
            failures += 1
        print("%-4s (exit %d) %-45s %s" % ("PASS" if ok else "FAIL", r.returncode, cmd, (r.stderr or "").strip()[:90]))
    total = len(SHOULD_BLOCK) + len(SHOULD_ALLOW)
    print("\n%d/%d tests passed" % (total - failures, total))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
