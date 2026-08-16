import os
import re
import sys
import subprocess
import logging
from datetime import datetime

HOOK_DIR = os.path.expanduser('~/.claude/hooks')
LOG_FILE = os.path.join(HOOK_DIR, 'blocked.log')
os.makedirs(HOOK_DIR, exist_ok=True)

# Destructive pattern rules
DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-(?:r[fv]|f[rv]|r|f)\s+(?:/|\.\.?/|\*|~|/\*|\$HOME)\b', "Catastrophic directory deletion"),
    (r'\bDROP\s+(?:DATABASE|TABLE|SCHEMA)\b', "Destructive SQL DROP"),
    (r'\bTRUNCATE\s+(?:TABLE\s+)?\w+', "Destructive SQL TRUNCATE"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?!WHERE\b)', "Unbounded SQL DELETE without WHERE clause"),
    (r'\bgit\s+push\s+.*(?:--force|-f)\s+.*(?:main|master|prod|release)', "Force push to protected branch"),
    (r':\(\)\s*\{\s*:\|:&\s*\};:', "Fork bomb detected")
]

# Safe scoped exceptions (e.g., clean build artifacts)
SAFE_WHITELIST = [
    r'rm\s+-(?:rf|fr|r|f)\s+(?:node_modules|\.next|dist|build|__pycache__|\.pytest_cache|\.turbo)(?:/|$)'
]

def log_blocked(command: str, project_path: str, reason: str):
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] REASON: {reason} | CMD: {command} | CWD: {project_path}\n")

def is_safe(command: str) -> bool:
    for pattern in SAFE_WHITELIST:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def evaluate_command(command: str, project_path: str) -> bool:
    if is_safe(command):
        return True

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, project_path, reason)
            print(f"\n[SECURITY BLOCK] Claude Code Hook intercepted dangerous operation:")
            print(f"  Reason  : {reason}")
            print(f"  Command : {command}")
            print(f"  Logged  : {LOG_FILE}\n")
            return False
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python pre-tool-use.py <command> <projectpath>")
        sys.exit(1)

    cmd = sys.argv[1]
    cwd = sys.argv[2]

    if not evaluate_command(cmd, cwd):
        sys.exit(2)  # Claude Code hook rejection signal

    # Allow normal execution
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    sys.exit(res.returncode)
                     
