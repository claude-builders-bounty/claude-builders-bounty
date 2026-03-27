#!/usr/bin/env python3
"""
Test script for the destructive command blocker hook.
Simulates Claude Code's pre-tool-use hook interface.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_command(command, should_block=True):
    """Test a command against the hook."""
    hook_path = Path(__file__).parent / 'pre-tool-use-block-destructive.py'
    
    # Create the hook input JSON
    request = {
        'tool': {
            'name': 'exec',
            'arguments': {
                'command': command
            }
        },
        'context': {
            'project_path': str(Path.cwd())
        }
    }
    
    # Run the hook
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(request),
        text=True,
        capture_output=True
    )
    
    try:
        response = json.loads(result.stdout)
        allowed = response.get('allow', True)
        message = response.get('message', '')
        
        if should_block:
            if not allowed:
                print(f"✅ PASS: '{command}' was correctly blocked")
                print(f"   Reason: {message.split(':')[1].split('\\n')[0] if ':' in message else 'Blocked'}")
                return True
            else:
                print(f"❌ FAIL: '{command}' was allowed (should be blocked)")
                return False
        else:
            if allowed:
                print(f"✅ PASS: '{command}' was correctly allowed")
                return True
            else:
                print(f"❌ FAIL: '{command}' was blocked (should be allowed)")
                print(f"   Reason: {message}")
                return False
                
    except json.JSONDecodeError:
        print(f"❌ ERROR: Hook returned invalid JSON: {result.stdout}")
        return False

def main():
    print("🧪 Testing Destructive Command Blocker Hook\n")
    
    tests = [
        # Dangerous commands (should be blocked)
        ("rm -rf /home/user", True),
        ("rm -rf node_modules", True),
        ("DROP TABLE users", True),
        ("TRUNCATE TABLE logs", True),
        ("DELETE FROM customers", True),
        ("git push --force origin main", True),
        ("git push -f", True),
        ("git reset --hard HEAD~1", True),
        ("chmod 777 /etc/passwd", True),
        (":(){ :|:& };:", True),  # Fork bomb
        
        # Safe commands (should be allowed)
        ("ls -la", False),
        ("git status", False),
        ("npm install", False),
        ("SELECT * FROM users WHERE id = 1", False),
        ("DELETE FROM users WHERE id = 1", False),  # Has WHERE clause
        ("echo 'Hello World'", False),
        ("python script.py", False),
        ("docker ps", False),
    ]
    
    passed = 0
    total = len(tests)
    
    for command, should_block in tests:
        if test_command(command, should_block):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    # Check log file was created
    log_file = Path.home() / '.claude' / 'hooks' / 'blocked.log'
    if log_file.exists():
        print(f"📝 Log file created at: {log_file}")
        # Show last few log entries
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("Last log entry:")
                    print(json.dumps(json.loads(lines[-1]), indent=2))
        except:
            pass
    
    if passed == total:
        print("\n🎉 All tests passed! Hook is ready for submission.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Review the hook implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())