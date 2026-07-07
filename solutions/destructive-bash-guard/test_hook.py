import subprocess
import sys
import json
import os

def run_hook(input_json):
    """Run pre-tool-use.py as a subprocess, passing input_json via stdin."""
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    hook_path = os.path.join(hook_dir, "pre-tool-use.py")
    res = subprocess.run(
        [sys.executable, hook_path],
        input=json.dumps(input_json).encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return res.returncode, res.stdout.decode('utf-8'), res.stderr.decode('utf-8')

def test_blocked_commands():
    blocked_cases = [
        # rm -rf cases
        {"command": "rm -rf /tmp/test"},
        {"command": "rm -f -r /tmp/test"},
        {"command": "rm --recursive --force /tmp/test"},
        {"command": "rm -fr /tmp/test"},
        # DROP TABLE cases
        {"command": "DROP TABLE users;"},
        {"command": "drop table if exists audits;"},
        # git push --force cases
        {"command": "git push origin main --force"},
        {"command": "git push -f"},
        # TRUNCATE cases
        {"command": "TRUNCATE TABLE access_logs;"},
        {"command": "truncate sessions;"},
        # DELETE FROM without WHERE cases
        {"command": "DELETE FROM users"},
        {"command": "delete   from   sessions;"},
    ]
    
    print("Running blocked cases...")
    for case in blocked_cases:
        code, stdout, stderr = run_hook(case)
        # Expected exit code for block is 2
        if code != 2:
            print(f"FAIL: Command '{case['command']}' was not blocked. Code: {code}, Msg: {stderr.strip()}")
            sys.exit(1)
        else:
            print(f"PASS: Blocked '{case['command']}' successfully. Message: {stderr.strip()}")

def test_allowed_commands():
    allowed_cases = [
        # rm cases (no force or no recursive)
        {"command": "rm file.txt"},
        {"command": "rm -r /tmp/dir"},
        {"command": "rm -f file.txt"},
        # git push cases (no force)
        {"command": "git push origin main"},
        {"command": "git push --force-with-lease"},
        # DELETE FROM with WHERE cases
        {"command": "DELETE FROM users WHERE id = 1"},
        {"command": "delete from sessions where expired = true;"},
        # General safe commands
        {"command": "ls -la"},
        {"command": "npm run build"},
        {"command": "python script.py"}
    ]
    
    print("\nRunning allowed cases...")
    for case in allowed_cases:
        code, stdout, stderr = run_hook(case)
        if code != 0:
            print(f"FAIL: Safe command '{case['command']}' was blocked. Code: {code}, Msg: {stderr.strip()}")
            sys.exit(1)
        else:
            print(f"PASS: Allowed '{case['command']}' successfully.")

if __name__ == "__main__":
    test_blocked_commands()
    test_allowed_commands()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
