import subprocess
import json
import os

TEST_CASES = [
    # True positives (should be blocked)
    ("rm -rf /", "deny"),
    ("rm -r -f .", "deny"),
    ("rm -fr /home", "deny"),
    ("rm --recursive --force /tmp", "deny"),
    ("echo 'hello'; rm -rf test", "deny"),
    ("DROP TABLE users;", "deny"),
    ("drop table orders", "deny"),
    ("git push origin main --force", "deny"),
    ("git push -f", "deny"),
    ("TRUNCATE TABLE logs;", "deny"),
    ("truncate my_table", "deny"),
    ("DELETE FROM users;", "deny"),
    ("delete from users", "deny"),
    
    # True negatives (should be allowed)
    ("rm -r mydir", "allow"),
    ("rm -f myfile", "allow"),
    ("echo 'rm -rf'", "allow"),
    ("git push origin main", "allow"),
    ("delete from users where id=1;", "allow"),
    ("DELETE FROM users WHERE name='test'", "allow"),
]

def run_test():
    passed = 0
    failed = 0
    for cmd, expected in TEST_CASES:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd},
            "cwd": "/tmp"
        }
        
        proc = subprocess.run(
            ["python", "destructive_guard.py"],
            input=json.dumps(payload),
            text=True,
            capture_output=True
        )
        
        try:
            output = json.loads(proc.stdout.strip())
            decision = output.get("decision")
            if decision == expected:
                print(f"[PASS] {cmd} -> {decision}")
                passed += 1
            else:
                print(f"[FAIL] {cmd} -> Expected {expected}, got {decision}")
                failed += 1
        except json.JSONDecodeError:
            print(f"[FAIL] {cmd} -> Invalid JSON output: {proc.stdout}")
            failed += 1
            
    print(f"\nResults: {passed} passed, {failed} failed.")
    
    # Check log file
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    if os.path.exists(log_path):
        print(f"\nLog file created at {log_path}")
        with open(log_path, "r") as f:
            lines = f.readlines()
            print(f"Total blocked entries in log: {len(lines)}")
            if len(lines) > 0:
                print("Last entry:", lines[-1].strip())
        # Clean up log for neatness
        os.remove(log_path)
    else:
        print("\nNo log file found.")

if __name__ == "__main__":
    run_test()
