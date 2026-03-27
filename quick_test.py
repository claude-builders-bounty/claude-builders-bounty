import json
import subprocess
import sys
from pathlib import Path

def test_command(cmd):
    """Test a single command against the hook."""
    hook_path = Path(__file__).parent / 'pre-tool-use-block-destructive.py'
    
    request = {
        'tool': {
            'name': 'exec',
            'arguments': {
                'command': cmd
            }
        },
        'context': {
            'project_path': str(Path.cwd())
        }
    }
    
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(request),
        text=True,
        capture_output=True
    )
    
    try:
        response = json.loads(result.stdout)
        return response.get('allow', True)
    except json.JSONDecodeError:
        return True

def main():
    print("Testing hook functionality...")
    
    # Test cases
    test_cases = [
        # (command, should_be_allowed)
        ("DELETE FROM customers", False),  # No WHERE clause
        ("DELETE FROM users WHERE id=1", True),  # Has WHERE clause
        ("DELETE FROM logs", False),  # No WHERE clause
        ("DELETE FROM products WHERE category='test'", True),  # Has WHERE clause
        ("rm -rf /home", False),
        ("DROP TABLE users", False),
        ("git push --force", False),
        ("ls -la", True),
        ("git status", True),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for cmd, should_allow in test_cases:
        allowed = test_command(cmd)
        if allowed == should_allow:
            print(f"✓ PASS: '{cmd[:40]}...' -> allowed={allowed}")
            passed += 1
        else:
            print(f"✗ FAIL: '{cmd[:40]}...' -> allowed={allowed}, expected={should_allow}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Hook is working correctly.")
        return 0
    else:
        print("Some tests failed. Check the hook implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())