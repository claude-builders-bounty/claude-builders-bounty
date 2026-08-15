import os
import re
import sys
import subprocess
import logging

os.makedirs(os.path.expanduser('~/.claude/hooks'), exist_ok=True)
logging.basicConfig(
    filename=os.path.expanduser('~/.claude/hooks/blocked.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

PATTERNS = [
    r'rm\s+-rf',
    r'DROP\s+TABLE',
    r'git\s+push\s+--force',
    r'TRUNCATE',
    r'DELETE\s+FROM\s+(?!.*WHERE)',
    r':\(\)\s*\{\s*:\|:&\s*\};:'
]

def pretooluse(command: str, projectpath: str) -> bool:
    for pattern in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            msg = f"Blocked command: '{command}' in project: {projectpath}"
            logging.info(msg)
            print(f"\n[SECURITY ALERT] Destructive command detected:\n  -> {command}")
            print("Command blocked by Claude Code pre-tool-use hook.\n")
            return False
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python pre-tool-use.py <command> <projectpath>")
        sys.exit(1)

    cmd = sys.argv[1]
    path = sys.argv[2]

    if not pretooluse(cmd, path):
        sys.exit(1)

    subprocess.run(cmd, shell=True)

if __name__ == '__main__':
    main()
  
