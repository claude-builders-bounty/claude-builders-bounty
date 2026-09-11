"""
Unit Tests for Claude Command Guard
"""
from hook import check_command

def test_guard():
    dangerous_commands = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs.ext4 /dev/sda1",
        "git push origin main --force",
        "DROP TABLE users;",
        "DROP DATABASE production;",
        "TRUNCATE TABLE logs;",
        "DELETE FROM customers;"
    ]

    safe_commands = [
        "ls -la",
        "git status",
        "git push origin main",
        "rm file.txt",
        "DELETE FROM users WHERE id = 5;",
        "npm test",
        "python app.py"
    ]

    for cmd in dangerous_commands:
        safe, _ = check_command(cmd)
        assert not safe, f"Failed to block dangerous command: {cmd}"

    for cmd in safe_commands:
        safe, _ = check_command(cmd)
        assert safe, f"Falsely blocked safe command: {cmd}"

    print("All 15 command guard security tests PASSED!")

if __name__ == "__main__":
    test_guard()
