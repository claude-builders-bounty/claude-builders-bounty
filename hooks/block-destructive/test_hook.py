#!/usr/bin/env python3
"""
Test suite for the destructive-command hook.
Runs check_command() against known blocked and allowed commands.
"""
import importlib.util, sys
from pathlib import Path

# Load hook module
spec = importlib.util.spec_from_file_location("hook", Path(__file__).parent / "block-destructive.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

passed = 0
failed = 0


def test(should_block: bool, command: str, label: str = ""):
    global passed, failed
    reason = hook.check_command(command)
    blocked = reason is not None
    ok = blocked == should_block
    icon = "✅" if ok else "❌"
    action = "BLOCKED" if blocked else "ALLOWED"
    print(f"  {icon} {action:7s}  {label or command}")
    if not ok:
        failed += 1
        if should_block:
            print(f"         ↳ expected BLOCK but got ALLOW")
        else:
            print(f"         ↳ false positive: {reason}")
    else:
        passed += 1


print("═══════════════════════════════════════════")
print(" Should BLOCK")
print("═══════════════════════════════════════════")
test(True, "rm -rf /", "rm -rf /")
test(True, "rm -rf /home/user/project", "rm -rf /home/user/project")
test(True, "rm -rf ./node_modules", "rm -rf ./node_modules")
test(True, "rm -fr /tmp/data", "rm -fr /tmp/data")
test(True, "rm -rfv /var/log", "rm -rfv /var/log")
test(True, "sudo rm -rf /opt/app", "sudo rm -rf /opt/app")
test(True, "sudo rm -rf .", "sudo rm -rf .")
test(True, "rm -rf *", "rm -rf *")
test(True, "DROP TABLE users", "DROP TABLE users")
test(True, "drop table sessions;", "drop table sessions;")
test(True, "DROP TABLE IF EXISTS logs;", "DROP TABLE IF EXISTS logs;")
test(True, "TRUNCATE TABLE orders", "TRUNCATE TABLE orders")
test(True, "TRUNCATE users", "TRUNCATE users (no TABLE)")
test(True, "DELETE FROM users", "DELETE FROM users (no WHERE)")
test(True, "DELETE FROM   logs;", "DELETE FROM logs; (no WHERE)")
test(True, "git push --force origin main", "git push --force")
test(True, "git push -f origin main", "git push -f")
test(True, "git push --force-with-lease", "git push --force-with-lease")
test(True, "git push origin main --force", "git push ... --force (trailing)")
test(True, "rm --recursive --force /tmp", "rm --recursive --force")
test(True, "rm --force --recursive /tmp", "rm --force --recursive")
test(True, "rm -R -f /tmp", "rm -R -f (uppercase R)")

print()
print("═══════════════════════════════════════════")
print(" Should ALLOW")
print("═══════════════════════════════════════════")
test(False, "ls -la", "ls -la")
test(False, "cat file.txt", "cat file.txt")
test(False, "rm file.txt", "rm single file (no flags)")
test(False, "rm -f lockfile.pid", "rm -f (no -r)")
test(False, "rm -r build/", "rm -r (no -f)")
test(False, "git push origin main", "git push (no force)")
test(False, "git status", "git status")
test(False, "git pull --rebase", "git pull --rebase")
test(False, "SELECT * FROM users", "SELECT query")
test(False, "DELETE FROM users WHERE id = 5", "DELETE FROM ... WHERE")
test(False, "DELETE FROM users WHERE name = 'test'", "DELETE FROM ... WHERE")
test(False, "echo 'rm -rf'", "echo containing rm -rf")
test(False, "python3 -c \"print('hello')\"", "python command")
test(False, "npm install", "npm install")
test(False, "docker build .", "docker build")
test(False, "mkdir -p /tmp/test", "mkdir -p")
test(False, "cp -r src/ dest/", "cp -r")
test(False, "mv old new", "mv")

print()
print(f"═══ Results: {passed} passed, {failed} failed ═══")
sys.exit(1 if failed else 0)
