#!/usr/bin/env python3
import sys, os, json, re, datetime

def load_payload():
    data = ''
    if not sys.stdin.isatty():
        data = sys.stdin.read()
    if not data and len(sys.argv) > 1:
        data = sys.argv[1]
    if not data:
        return {}
    try:
        return json.loads(data)
    except Exception:
        return {}

def log_block(command, rule):
    log_dir = os.path.expanduser('~/.claude/hooks')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'blocked.log')
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    cwd = os.getcwd()
    entry = f"{ts} | CMD: {command} | RULE: {rule} | CWD: {cwd}\n"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)

def block_message(rule, suggestion):
    msg = (f"Command blocked by safety hook: matched rule '{rule}'. "
           f"Suggested safer alternative: {suggestion}")
    sys.stderr.write(msg + "\n")
    sys.stdout.write(msg + "\n")

def has_rm_rf(cmd):
    # detect rm with both -r and -f in any form
    if not re.search(r'\brm\b', cmd, re.I):
        return False
    opts = re.findall(r'\brm\s+([-\w\s]+)', cmd, re.I)
    for opt in opts:
        opt = opt.replace(' ', '')
        if 'r' in opt and 'f' in opt:
            return True
    return False

def has_delete_without_where(cmd):
    if not re.search(r'\bDELETE\s+FROM\b', cmd, re.I):
        return False
    # remove anything after a semicolon to avoid multi‑command tricks
    part = cmd.split(';')[0]
    return not re.search(r'\bWHERE\b', part, re.I)

def main():
    payload = load_payload()
    tool = payload.get('tool_name', '')
    command = payload.get('tool_input', {}).get('command', '')

    if tool != 'Bash' or not command:
        sys.exit(0)

    patterns = [
        ('rm -rf pattern', lambda c: has_rm_rf(c)),
        ('DROP TABLE/DATABASE', lambda c: re.search(r'\bDROP\s+(TABLE|DATABASE)\b', c, re.I)),
        ('git push --force', lambda c: re.search(r'\bgit\s+push\s+(?:--force|-f)\b', c, re.I)),
        ('TRUNCATE', lambda c: re.search(r'\bTRUNCATE\b', c, re.I)),
        ('DELETE without WHERE', lambda c: has_delete_without_where(c)),
    ]

    for rule, checker in patterns:
        if checker(command):
            log_block(command, rule)
            suggestions = {
                'rm -rf pattern': "Use specific file paths and avoid -r/-f together.",
                'DROP TABLE/DATABASE': "Consider backing up data before dropping.",
                'git push --force': "Use a regular push or create a new branch.",
                'TRUNCATE': "Delete specific rows or backup before truncating.",
                'DELETE without WHERE': "Add a WHERE clause to limit deletions."
            }
            block_message(rule, suggestions.get(rule, 'review the command'))
            sys.exit(2)

    sys.exit(0)

if __name__ == '__main__':
    main()
