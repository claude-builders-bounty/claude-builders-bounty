import subprocess
import json
import io
import os

def run_hook(tool_name, arguments):
    input_data = json.dumps({
        "tool": tool_name,
        "arguments": arguments
    })

    # Use relative path to the hook script
    hook_path = os.path.join(os.path.dirname(__file__), 'pre-tool-use.py')

    process = subprocess.Popen(
        ['python', hook_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(input=input_data)
    if stderr:
        print(f"Error: {stderr}")
    return json.loads(stdout)

# Test cases
test_cases = [
    ("bash", {"command": "ls -la"}, "allow"),
    ("bash", {"command": "rm -rf /data"}, "deny"),
    ("bash", {"command": "rm -r -f /data"}, "deny"),
    ("bash", {"command": "git push origin main --force"}, "deny"),
    ("bash", {"command": "git push -f origin main"}, "deny"),
    ("bash", {"command": "DROP TABLE users;"}, "deny"),
    ("bash", {"command": "DELETE FROM logs"}, "deny"),
    ("bash", {"command": "DELETE FROM logs WHERE id=1"}, "allow"),
    ("bash", {"command": "rm -rf /"}, "deny"),
    ("not_bash", {"command": "rm -rf /"}, "allow"), # Should only block bash
]

for tool, args, expected in test_cases:
    result = run_hook(tool, args)
    action = result.get("action")
    print(f"Testing '{args.get('command')}': Expected {expected}, Got {action} - {'PASS' if action == expected else 'FAIL'}")
    if action == "deny":
        print(f"  Message: {result.get('message')}")
