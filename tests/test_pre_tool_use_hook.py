#!/usr/bin/env python3
"""
Unit tests for the pre-tool-use hook.

Tests both blocked and allowed commands to ensure the hook:
1. Blocks dangerous patterns correctly
2. Allows safe commands to pass through
3. Handles edge cases and variations
"""

import json
import subprocess
import tempfile
import os
import sys


class HookTester:
    """Helper class to test the pre-tool-use hook."""

    def __init__(self, hook_path):
        self.hook_path = hook_path

    def test_command(self, command, should_block=False):
        """
        Test a bash command against the hook.

        Args:
            command: Bash command to test
            should_block: Whether the command should be blocked

        Returns:
            bool: True if test passed, False if failed
        """
        input_data = {
            "tool_name": "bash",
            "tool_input": {"command": command},
            "project_path": "/home/test/project"
        }

        try:
            proc = subprocess.run(
                [sys.executable, self.hook_path],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=5
            )

            if proc.returncode != 0:
                print(f"  ✗ {command}")
                print(f"    Error: {proc.stderr}")
                return False

            result = json.loads(proc.stdout)
            decision = result.get("permissionDecision", "unknown")

            expected_decision = "deny" if should_block else "allow"
            passed = decision == expected_decision

            status = "✓" if passed else "✗"
            print(f"  {status} {command} → {decision}")

            return passed

        except json.JSONDecodeError as e:
            print(f"  ✗ {command}")
            print(f"    Invalid JSON response: {proc.stdout}")
            return False
        except Exception as e:
            print(f"  ✗ {command}")
            print(f"    Error: {e}")
            return False


def main():
    """Run all hook tests."""
    hook_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "hooks",
        "pre_tool_use.py"
    )

    if not os.path.exists(hook_path):
        print(f"Error: Hook not found at {hook_path}")
        sys.exit(1)

    tester = HookTester(hook_path)
    results = []

    print("\n" + "=" * 60)
    print("Testing Pre-tool-use Hook")
    print("=" * 60)

    # Test 1: rm -rf (should block)
    print("\n1. Testing 'rm -rf' patterns (SHOULD BLOCK)")
    results.append(tester.test_command("rm -rf /tmp", should_block=True))
    results.append(tester.test_command("rm -rf /tmp/data", should_block=True))
    results.append(tester.test_command("rm -rf /", should_block=True))
    results.append(tester.test_command("rm -fr /tmp", should_block=True))
    results.append(tester.test_command("rm -rf", should_block=True))

    # Test 2: rm safe patterns (should allow)
    print("\n2. Testing 'rm' safe patterns (SHOULD ALLOW)")
    results.append(tester.test_command("rm file.txt", should_block=False))
    results.append(tester.test_command("rm -r directory", should_block=False))
    results.append(tester.test_command("rm data.json", should_block=False))
    results.append(tester.test_command("rm *.tmp", should_block=False))

    # Test 3: DROP TABLE (should block)
    print("\n3. Testing 'DROP TABLE' patterns (SHOULD BLOCK)")
    results.append(tester.test_command("DROP TABLE users", should_block=True))
    results.append(tester.test_command("drop table users", should_block=True))
    results.append(tester.test_command("DROP TABLE IF EXISTS users", should_block=True))
    results.append(tester.test_command("DROP DATABASE mydb", should_block=True))

    # Test 4: TRUNCATE (should block)
    print("\n4. Testing 'TRUNCATE' patterns (SHOULD BLOCK)")
    results.append(tester.test_command("TRUNCATE TABLE users", should_block=True))
    results.append(tester.test_command("truncate table sessions", should_block=True))

    # Test 5: DELETE without WHERE (should block)
    print("\n5. Testing 'DELETE FROM' without WHERE (SHOULD BLOCK)")
    results.append(tester.test_command("DELETE FROM users", should_block=True))
    results.append(tester.test_command("delete from sessions", should_block=True))

    # Test 6: DELETE with WHERE (should allow)
    print("\n6. Testing 'DELETE FROM' with WHERE (SHOULD ALLOW)")
    results.append(tester.test_command("DELETE FROM users WHERE id = 1", should_block=False))
    results.append(tester.test_command("DELETE FROM users WHERE email = 'test@example.com'", should_block=False))
    results.append(tester.test_command("delete from sessions where created_at < '2020-01-01'", should_block=False))

    # Test 7: git push --force (should block)
    print("\n7. Testing 'git push --force' patterns (SHOULD BLOCK)")
    results.append(tester.test_command("git push --force origin main", should_block=True))
    results.append(tester.test_command("git push -f origin main", should_block=True))
    results.append(tester.test_command("git push --force-with-lease origin main", should_block=True))
    results.append(tester.test_command("git push --force", should_block=True))

    # Test 8: git push safe (should allow)
    print("\n8. Testing 'git push' safe patterns (SHOULD ALLOW)")
    results.append(tester.test_command("git push origin main", should_block=False))
    results.append(tester.test_command("git push", should_block=False))
    results.append(tester.test_command("git push origin HEAD", should_block=False))

    # Test 9: Normal commands (should allow)
    print("\n9. Testing normal safe commands (SHOULD ALLOW)")
    results.append(tester.test_command("echo hello", should_block=False))
    results.append(tester.test_command("npm test", should_block=False))
    results.append(tester.test_command("python script.py", should_block=False))
    results.append(tester.test_command("ls -la", should_block=False))

    # Test 10: Edge cases
    print("\n10. Testing edge cases (SHOULD HANDLE GRACEFULLY)")
    results.append(tester.test_command("", should_block=False))
    results.append(tester.test_command("   ", should_block=False))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\nResults: {passed}/{total} tests passed ({percentage:.0f}%)")

    if passed == total:
        print("✓ All tests passed! Hook is working correctly.")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed. Review above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
