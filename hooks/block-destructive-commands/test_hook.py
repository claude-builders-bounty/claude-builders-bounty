#!/usr/bin/env python3
import subprocess
import os

TEST_CASES = [
    # (command, should_block, expected_reason_keyword)
    ("rm -rf /tmp/myproject", True, "Recursive force deletion"),
    ("rm -fr dist", True, "Recursive force deletion"),
    ("DROP TABLE users;", True, "DROP TABLE"),
    ("TRUNCATE orders;", True, "TRUNCATE"),
    ("git push origin main --force", True, "force push"),
    ("git push origin main -f", True, "force push"),
    ("DELETE FROM sessions;", True, "WHERE"),
    
    # Safe commands that must pass:
    ("ls -la", False, ""),
    ("npm run build", False, ""),
    ("git commit -m 'fix bug'", False, ""),
    ("git push origin main", False, ""),
    ("DELETE FROM users WHERE id = 5;", False, ""),
    ("cat README.md", False, ""),
    ("rm single_file.txt", False, "")
]

def run_tests():
    script_path = os.path.abspath("pre_tool_use.py")
    passed = 0
    failed = 0

    print("=" * 70)
    print("🧪 RUNNING PRE-TOOL-USE SECURITY HOOK TEST SUITE")
    print("=" * 70)

    for cmd, should_block, reason_kw in TEST_CASES:
        res = subprocess.run(
            ["python3", script_path, cmd],
            capture_output=True,
            text=True
        )
        is_blocked = (res.returncode != 0)
        
        if is_blocked == should_block:
            status = "✅ PASS"
            passed += 1
            if should_block:
                print(f"{status} [BLOCKED]: '{cmd}' -> Caught: {reason_kw}")
            else:
                print(f"{status} [ALLOWED]: '{cmd}'")
        else:
            status = "❌ FAIL"
            failed += 1
            print(f"{status}: '{cmd}' (Expected blocked={should_block}, got {is_blocked})")

    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{len(TEST_CASES)} Passed, {failed} Failed.")
    print("=" * 70)
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
