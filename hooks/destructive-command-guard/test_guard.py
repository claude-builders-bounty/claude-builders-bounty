#!/usr/bin/env python3
"""Tests for the Destructive Command Guard hook."""

import json
import os
import sys
import tempfile

# Add the hook directory to path so we can import guard
sys.path.insert(0, os.path.dirname(__file__))
from guard import check_command

# ── Tests ─────────────────────────────────────────────────────────────────

SHOULD_BLOCK = [
    # Filesystem destruction
    ("rm -rf /", "rm -rf root"),
    ("rm -rf ~/*", "rm -rf home"),
    ("rm -rf .", "rm -rf current dir"),
    ("rm -rfi /*", "rm -rf with interactive flag mixed"),
    ("sudo rm -rf /var", "sudo rm -rf"),
    
    # SQL destruction
    ("DROP TABLE users;", "DROP TABLE"),
    ("drop table IF EXISTS orders;", "DROP TABLE case insensitive"),
    ("DROP DATABASE production;", "DROP DATABASE"),
    ("TRUNCATE TABLE logs;", "TRUNCATE TABLE"),
    ("TRUNCATE sessions;", "TRUNCATE without TABLE keyword"),
    ("DELETE FROM users;", "DELETE FROM without WHERE"),
    ("DELETE FROM users WHERE 1=1", "DELETE FROM with always-true WHERE"),
    
    # Git force operations
    ("git push --force", "git push force"),
    ("git push -f origin main", "git push -f"),
    ("git push origin main --force", "git push force at end"),
    ("git reset --hard HEAD~5", "git reset hard"),
    ("git clean -fd", "git clean force directories"),
    ("git clean -df", "git clean reversed flags"),
    
    # System-level
    ("mkfs.ext4 /dev/sda1", "mkfs"),
    ("dd if=/dev/zero of=/dev/sda", "dd to device"),
    ("chmod -R 777 /", "chmod 777 root"),
    ("docker system prune -a", "docker prune all"),
]

SHOULD_ALLOW = [
    # Normal file operations
    ("rm file.txt", "single file removal"),
    ("rm -f temp.log", "force remove single file"),
    ("rm -r ./node_modules", "rm -r without -f on specific dir"),
    
    # Safe SQL
    ("DELETE FROM users WHERE id = 5;", "DELETE with specific WHERE"),
    ("SELECT * FROM users;", "SELECT query"),
    ("INSERT INTO users (name) VALUES ('test');", "INSERT"),
    ("UPDATE users SET name = 'test' WHERE id = 1;", "UPDATE with WHERE"),
    ("DROP TABLE", "incomplete DROP — no table name"),
    
    # Safe git
    ("git push origin main", "normal git push"),
    ("git push", "simple git push"),
    ("git pull --rebase", "git pull rebase"),
    ("git reset --soft HEAD~1", "soft reset"),
    ("git stash", "git stash"),
    ("git clean -n", "git clean dry run"),
    
    # Normal commands
    ("ls -la", "list files"),
    ("cat /etc/hosts", "read file"),
    ("echo 'hello world'", "echo"),
    ("python3 script.py", "run python"),
    ("npm install", "npm install"),
    ("docker build -t myapp .", "docker build"),
    ("docker system prune", "docker prune without -a"),
]


def run_tests():
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("Destructive Command Guard — Test Suite")
    print("=" * 60)
    
    print("\n--- Commands that SHOULD be blocked ---")
    for cmd, desc in SHOULD_BLOCK:
        blocked, reason = check_command(cmd)
        status = "PASS" if blocked else "FAIL"
        if blocked:
            passed += 1
            print(f"  [{status}] {desc}: blocked ({reason[:40]}...)")
        else:
            failed += 1
            print(f"  [{status}] {desc}: NOT blocked! Command: {cmd}")
    
    print("\n--- Commands that should be ALLOWED ---")
    for cmd, desc in SHOULD_ALLOW:
        blocked, reason = check_command(cmd)
        status = "PASS" if not blocked else "FAIL"
        if not blocked:
            passed += 1
            print(f"  [{status}] {desc}: allowed")
        else:
            failed += 1
            print(f"  [{status}] {desc}: incorrectly blocked! Reason: {reason}")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
