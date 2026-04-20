# Claude Code Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Features

Blocks the following destructive patterns:
- `rm -rf` - recursive force delete
- `DROP TABLE` - database table deletion
- `git push --force` - forced push to remote
- `TRUNCATE` - table truncation
- `DELETE FROM` without a WHERE clause - unconditional row deletion

## Installation

1. Copy `block_destructive.py` to your Claude Code hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   cp block_destructive.py ~/.claude/hooks/
   chmod +x ~/.claude/hooks/block_destructive.py
   ```

2. Add the hook to your `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "pre-tool-use": "~/.claude/hooks/block_destructive.py"
     }
   }
   ```

## How It Works

The hook receives JSON input from Claude Code's tool execution pipeline. It:
1. Parses the incoming tool request
2. Checks the command against destructive patterns
3. If a match is found, logs the attempt and returns a blocking response
4. If no match, allows execution to proceed

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO format)
- Username
- Reason blocked
- Full command

Example log entry:
```
[2026-04-20T20:14:30.123456] user=kasion blocked=rm -rf (recursive force delete) command=rm -rf /important/files
```

## Testing

Test the hook directly:
```bash
echo '{"tool": "bash", "command": "rm -rf /tmp/test"}' | python3 block_destructive.py
echo '{"tool": "bash", "command": "ls -la"}' | python3 block_destructive.py
```

## File Structure

```
claude-builders-bounty/
├── hooks/
│   └── pre-tool-use/
│       ├── block_destructive.py   # Main hook script
│       └── README.md              # This file
├── workflows/
└── README.md
```