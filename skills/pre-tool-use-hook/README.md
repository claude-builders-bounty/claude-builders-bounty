# Claude Code Pre-Tool-Use Hook

A Python hook that blocks destructive bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_hook.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Features

✅ Blocks dangerous patterns:
- `rm -rf` (recursive delete)
- `DROP TABLE` (database)
- `git push --force` (force push)
- `TRUNCATE` (database)
- `DELETE FROM` without WHERE clause
- Fork bombs and device writes

✅ Logs all blocked attempts to `~/.claude/hooks/blocked.log`

✅ Shows clear warning message

✅ Non-intrusive - doesn't affect normal commands

## Usage

Once installed, Claude Code will automatically check commands before execution.

If a dangerous command is detected:
```
⚠️  BLOCKED: Destructive command detected!
   Command: rm -rf /important/data
   Project: /home/user/project
   
   This command matches a blocked pattern.
   See blocked.log for details.
```

## View Blocked Commands

```bash
cat ~/.claude/hooks/blocked.log
```

## How It Works

1. Claude Code calls the pre-tool-use hook before executing bash commands
2. Hook checks command against blocked patterns
3. If match found: logs attempt and blocks execution
4. If safe: allows execution to proceed

## Customization

Edit `BLOCKED_PATTERNS` in `pre_tool_hook.py` to add/remove patterns.