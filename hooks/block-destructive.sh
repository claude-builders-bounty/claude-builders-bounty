#!/usr/bin/env python3
import os, sys, re, datetime

P1 = r'rm\s+-rf\s+/'
P2 = r'DROP\s+TABLE'
P3 = r'git\s+push\s+--force'
P4 = r'TRUNCATE\s+'
P5 = r'DELETE\s+FROM\s+\w+(?!\s+WHERE)'

BLOCK_PATTERNS = [P1, P2, P3, P4, P5]

input_data = sys.stdin.read()
pattern5_obj = re.compile(P5)
cmd_match = pattern5_obj.search(input_data)
if not cmd_match:
    sys.exit(0)

command = cmd_match.group(1)
blocked = False
reason = ''
for p in BLOCK_PATTERNS:
    if re.search(p, command, re.IGNORECASE):
        blocked = True
        reason = p
        break

if blocked:
    log_dir = os.path.expanduser('~/.claude/hooks')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'blocked.log')
    ts = datetime.datetime.now().isoformat()
    with open(log_file, 'a') as f:
        f.write('[' + ts + '] BLOCKED: ' + command + ' (pattern: ' + reason + ')\n')
    print('HOOK_BLOCKED: Command blocked - ' + reason, file=sys.stderr)
    sys.exit(1)

sys.exit(0)
