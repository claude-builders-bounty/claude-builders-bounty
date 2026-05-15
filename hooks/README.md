# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Installation

```bash
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

- `rm -rf` — recursive force deletion
- `DROP TABLE` — database table destruction
- `git push --force` — history rewrite
- `TRUNCATE TABLE` — irreversible table emptying
- `DELETE FROM` without `WHERE` — mass row deletion

## How It Works

When a bash tool call is intercepted, the hook:
1. Parses the command from the tool-use payload
2. Checks against dangerous patterns
3. Logs blocked attempts to `~/.claude/hooks/blocked.log`
4. Returns a clear message to Claude explaining why the command was blocked

## Requirements

- Python 3.6+
- Claude Code with hooks support

## Verification

```bash
cd /tmp/claude-builders-bounty
python3 -c "
import json, subprocess, os, tempfile
os.chdir(tempfile.mkdtemp())
payload = json.dumps({'tool_use': {'tool': 'bash', 'command': 'rm -rf /important'}})
result = subprocess.run(['python3', '/tmp/claude-builders-bounty/hooks/pre-tool-use'], input=payload, capture_output=True, text=True)
print('STDERR:', result.stderr[:200])
print('RETURN:', result.returncode)
assert result.returncode == 1, 'Should block rm -rf'
print('✅ rm -rf blocked')

payload = json.dumps({'tool_use': {'tool': 'bash', 'command': 'echo hello'}})
result = subprocess.run(['python3', '/tmp/claude-builders-bounty/hooks/pre-tool-use'], input=payload, capture_output=True, text=True)
assert result.returncode == 0, 'Should allow safe command'
print('✅ safe command allowed')

payload = json.dumps({'tool_use': {'tool': 'bash', 'command': 'DELETE FROM users'}})
result = subprocess.run(['python3', '/tmp/claude-builders-bounty/hooks/pre-tool-use'], input=payload, capture_output=True, text=True)
assert result.returncode == 1, 'Should block DELETE without WHERE'
print('✅ DELETE without WHERE blocked')

payload = json.dumps({'tool_use': {'tool': 'bash', 'command': 'DELETE FROM users WHERE id=1'}})
result = subprocess.run(['python3', '/tmp/claude-builders-bounty/hooks/pre-tool-use'], input=payload, capture_output=True, text=True)
assert result.returncode == 0, 'Should allow DELETE with WHERE'
print('✅ DELETE with WHERE allowed')
"
```
