#!/usr/bin/env python3
"""Test script for the pre-tool-use destructive command blocker hook."""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "hooks" / "pre-tool-use"

PASS = 0
FAIL = 0

def test_block(desc, payload_str):
    global PASS, FAIL
    if payload_str:
        proc = subprocess.run(
            [str(HOOK)],
            input=payload_str,
            capture_output=True,
            text=True,
            timeout=5,
        )
    else:
        proc = subprocess.run(
            [str(HOOK)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    if proc.returncode == 1:
        print(f"  PASS: {desc}")
        PASS += 1
    else:
        print(f"  FAIL: {desc} (exit {proc.returncode}, expected 1)")
        if proc.stderr:
            print(f"       stderr: {proc.stderr.strip()[:200]}")
        FAIL += 1

def test_allow(desc, payload_str):
    global PASS, FAIL
    if payload_str:
        proc = subprocess.run(
            [str(HOOK)],
            input=payload_str,
            capture_output=True,
            text=True,
            timeout=5,
        )
    else:
        proc = subprocess.run(
            [str(HOOK)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    if proc.returncode == 0:
        print(f"  PASS: {desc}")
        PASS += 1
    else:
        print(f"  FAIL: {desc} (exit {proc.returncode}, expected 0)")
        if proc.stderr:
            print(f"       stderr: {proc.stderr.strip()[:200]}")
        FAIL += 1

print("=== Destructive (expect BLOCK) ===")
test_block("rm -rf",                '{"command":"rm -rf /tmp/build"}')
test_block("rm -rf with sudo",      '{"command":"sudo rm -rf --no-preserve-root /"}')
test_block("DROP TABLE",            '{"command":"DROP TABLE users;"}')
test_block("drop table lower",      '{"command":"drop table if exists orders;"}')
test_block("DROP DATABASE",         '{"command":"DROP DATABASE production;"}')
test_block("TRUNCATE",              '{"command":"TRUNCATE logs;"}')
test_block("DELETE no WHERE",       '{"command":"DELETE FROM users;"}')
test_block("git push --force",      '{"command":"git push --force origin main"}')
test_block("git push -f",           '{"command":"git push -f origin main"}')
test_block("rm -rf via wrapped",    '{"tool":"Bash","args":{"command":"rm -rf /tmp"}}')

print()
print("=== Safe (expect ALLOW) ===")
test_allow("ls -la",                '{"command":"ls -la"}')
test_allow("rm file",               '{"command":"rm file.txt"}')
test_allow("rm -r (no -f)",         '{"command":"rm -r tempdir"}')
test_allow("git push normal",       '{"command":"git push origin main"}')
test_allow("git push no args",      '{"command":"git push"}')
test_allow("DELETE with WHERE id",  '{"command":"DELETE FROM users WHERE id = 5;"}')
test_allow("DELETE with WHERE IS NULL", '{"command":"DELETE FROM users WHERE deleted_at IS NULL;"}')
test_allow("SELECT",                '{"command":"SELECT * FROM users"}')
test_allow("CREATE TABLE",          '{"command":"CREATE TABLE temp (id int);"}')
test_allow("wrapped safe tool",     '{"tool":"Bash","args":{"command":"ls -la"}}')

print()
print("=== Edge cases ===")
test_allow("no stdin (empty)",      "")
test_allow("malformed JSON",        "not-json-at-all")
test_allow("JSON scalar",           "123")
test_allow("empty command",         '{"command":""}')
test_allow("nested toolUse format", '{"toolUse":{"name":"Bash","input":{"command":"echo hello"}}}')

print()
print(f"Results: {PASS} passed, {FAIL} failed")

# Print blocked log
logpath = os.path.expanduser("~/.claude/hooks/blocked.log")
if os.path.exists(logpath):
    print(f"\n=== Blocked log ({logpath}) ===")
    with open(logpath) as f:
        print(f.read())

sys.exit(0 if FAIL == 0 else 1)
