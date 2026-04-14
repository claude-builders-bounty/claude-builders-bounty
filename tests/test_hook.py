#!/usr/bin/env python3
"""Test the destructive command blocker hook."""

import json
import sys
import os
import tempfile

# Add the hooks directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_blocks_rm_rf():
    """Test that rm -rf is blocked."""
    from hook import main, BLOCKED_PATTERNS
    import re
    
    dangerous_commands = [
        "rm -rf /tmp/test",
        "rm -r -f /some/path",
        "rm --recursive --force /data",
        "DROP TABLE users",
        "git push --force origin main",
        "TRUNCATE TABLE logs",
        "DELETE FROM users WHERE 1=1",
    ]
    
    safe_commands = [
        "ls -la",
        "rm file.txt",
        "git push origin main",
        "python script.py",
        "npm install",
    ]
    
    for cmd in dangerous_commands:
        blocked = False
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                blocked = True
                break
        assert blocked, f"Should block: {cmd}"
    
    for cmd in safe_commands:
        blocked = False
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                blocked = True
                break
        assert not blocked, f"Should NOT block: {cmd}"
    
    print("✅ All hook tests passed!")

if __name__ == "__main__":
    test_blocks_rm_rf()
