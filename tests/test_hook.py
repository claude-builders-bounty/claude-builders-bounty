#!/usr/bin/env python3
"""Test the destructive command blocker hook."""

import sys
import os
import re

# Add the hooks directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hooks'))

from hook import BLOCKED_PATTERNS

def test_patterns():
    """Test pattern matching for dangerous and safe commands."""
    
    dangerous_commands = [
        "rm -rf /tmp/test",
        "rm -r -f /some/path",
        "rm --recursive --force /data",
        "DROP TABLE users",
        "git push --force origin main",
        "TRUNCATE TABLE logs",
        "DELETE FROM users",  # No WHERE
    ]
    
    safe_commands = [
        "ls -la",
        "rm file.txt",
        "git push origin main",
        "python script.py",
        "npm install",
    ]
    
    print("Testing dangerous commands...")
    for cmd in dangerous_commands:
        blocked = False
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                blocked = True
                print(f"  ✅ BLOCKED: {cmd} -> {reason}")
                break
        if not blocked:
            print(f"  ❌ MISSED: {cmd}")
    
    print("\nTesting safe commands...")
    for cmd in safe_commands:
        blocked = False
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                blocked = True
                print(f"  ❌ FALSE POSITIVE: {cmd}")
                break
        if not blocked:
            print(f"  ✅ ALLOWED: {cmd}")
    
    print("\n✅ Tests complete!")

if __name__ == "__main__":
    test_patterns()
