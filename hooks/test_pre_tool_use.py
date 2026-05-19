#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the hooks directory to path so we can import pre-tool-use
sys.path.append(str(Path(__file__).parent))
import importlib.util

# Import the module dynamically because it has a hyphen in the filename
spec = importlib.util.spec_from_file_location("pre_tool_use", Path(__file__).parent / "pre-tool-use.py")
pre_tool_use = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pre_tool_use)

def run_tests():
    test_cases = [
        # Git Push Force tests
        ("git push origin main --force", True, "git push --force"),
        ("git push --force", True, "git push --force"),
        ("git push origin main --force-with-lease", False, None),
        ("git push --force-with-lease", False, None),
        ("git push -f", False, None),  # Not blocked under our current rules since it checks --force
        ("git push origin main --force --force-with-lease", False, None), # Should allow lease

        # rm -rf / rm -fr tests
        ("rm -rf /tmp/test", True, "rm -rf"),
        ("rm -fr /tmp/test", True, "rm -rf"),
        ("rm -r -f /tmp/test", True, "rm -rf"),
        ("rm -f -r /tmp/test", True, "rm -rf"),
        ("rm --recursive --force /tmp/test", True, "rm -rf"),
        ("rm -r /tmp/test", False, None),
        ("rm -f /tmp/test", False, None),
        ("rm /tmp/test", False, None),
        ("/usr/bin/rm -rf /tmp/test", True, "rm -rf"),
        # Separate commands with a pipe or separator
        ("rm -f /tmp/test && rm -r /tmp/test", False, None), # separated, so neither single command has both -r and -f in the same rm token sequence
        ("rm -rf /tmp/test; ls", True, "rm -rf"),

        # DROP TABLE tests
        ("DROP TABLE users", True, "DROP TABLE"),
        ("DROP TABLE IF EXISTS logs", True, "DROP TABLE"),
        ("drop table my_schema.users", True, "DROP TABLE"),
        ("SELECT * FROM users", False, None),

        # TRUNCATE tests
        ("TRUNCATE TABLE users", True, "TRUNCATE"),
        ("TRUNCATE logs", True, "TRUNCATE"),
        ("truncate table `my-db`.users", True, "TRUNCATE"),

        # DELETE FROM no WHERE tests
        ("DELETE FROM users", True, "DELETE FROM (no WHERE)"),
        ("DELETE FROM users WHERE id = 1", False, None),
        ("delete from schema.users where age > 30", False, None),
        ("DELETE FROM users; SELECT * FROM users", True, "DELETE FROM (no WHERE)"),
        # Multi-command checks
        ("DELETE FROM users; -- comment", True, "DELETE FROM (no WHERE)"),
        ("DELETE FROM users WHERE 1=1", False, None),
    ]

    failed = 0
    print("Running check_destructive hook tests...")
    print("=" * 60)
    for cmd, expected_blocked, expected_pattern in test_cases:
        res = pre_tool_use.check_destructive(cmd)
        blocked = res["blocked"]
        pattern = res["pattern"]
        if blocked != expected_blocked or (expected_blocked and pattern != expected_pattern):
            print(f"FAIL: {cmd!r}")
            print(f"  Expected: blocked={expected_blocked}, pattern={expected_pattern!r}")
            print(f"  Got:      blocked={blocked}, pattern={pattern!r}")
            failed += 1
        else:
            status = "BLOCKED" if blocked else "ALLOWED"
            print(f"PASS: [{status}] {cmd!r}")

    print("=" * 60)
    if failed == 0:
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"{failed} TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
