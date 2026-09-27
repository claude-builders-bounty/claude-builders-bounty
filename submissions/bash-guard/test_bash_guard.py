import json, subprocess, os, sys
HOOK = "bash-guard.py"  # same directory
CASES = [
    # (command, should_block)
    ("rm -rf /tmp/foo", True),
    ("rm -rf node_modules", True),
    ("sudo rm -rf /", True),
    ("rm -f file.txt", False),
    ("rm file.txt", False),
    ("rm -r olddir", False),
    ('psql -c "DROP TABLE users;"', True),
    ('mysql -e "drop database prod"', True),
    ('psql -c "DELETE FROM users;"', True),
    ('psql -c "DELETE FROM users WHERE id=3;"', False),
    ('psql -c "TRUNCATE TABLE logs;"', True),
    ("git push --force origin main", True),
    ("git push -f", True),
    ("git push --force-with-lease", True),
    ("git push origin main", False),
    ("git push --follow-tags", False),
    ("ls -la", False),
    ("echo 'rm -rf is dangerous' > note.txt", False),  # quoted text, not execution
    ("npm run build", False),
    ("docker compose up -d", False),
    ("git commit -m 'fix rm -rf handling'", False),  # commit message text only
]
fails = 0
for cmd, expect in CASES:
    payload = json.dumps({"tool_input": {"command": cmd}, "cwd": "/tmp/proj"})
    r = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True)
    blocked = (r.returncode == 2)
    ok = (blocked == expect)
    if not ok: fails += 1
    print(f"{'OK ' if ok else 'XX '} block={blocked!s:5} expect={expect!s:5} | {cmd}")
print(f"\n{len(CASES)-fails}/{len(CASES)} passed")
sys.exit(1 if fails else 0)
