#!/usr/bin/env python3
"""Test suite for pre-tool-use hook."""
import subprocess
import json

tests = [
    ("ls -la", "allow"),
    ("rm -rf /tmp/test", "block"),
    ("git push --force origin main", "block"),
    ("mysql -e 'DROP TABLE users'", "block"),
    ("psql -c 'DELETE FROM sessions'", "block"),
    ("echo 'rm -rf is dangerous'", "allow"),
    ("chmod -R 777 /var/www", "block"),
    ("cat /etc/hosts", "allow"),
    ("npm install", "allow"),
    ("dd if=/dev/zero of=/dev/sda", "block"),
    ("mkfs.ext4 /dev/sdb1", "block"),
    ("shutdown now", "block"),
]

passed = 0
failed = 0

for cmd, expected in tests:
    input_data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    r = subprocess.run(
        ["python3", "bounty3-pre-tool-use-hook/pre-tool-use-hook.py"],
        input=input_data, capture_output=True, text=True
    )
    result = json.loads(r.stdout.strip()) if r.stdout.strip() else {}
    decision = result.get("decision", "ERROR")
    status = "PASS" if decision == expected else "FAIL"
    if decision == expected:
        passed += 1
    else:
        failed += 1
    print(f"  {status} | {cmd:45s} → {decision:6s} (expected: {expected})")

print(f"\n{passed}/{len(tests)} passed, {failed} failed")
exit(1 if failed else 0)
