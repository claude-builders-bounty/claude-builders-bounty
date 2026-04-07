# Pre-tool-use Hook: Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## Install

```bash
# Copy hook to Claude Code hooks directory
cp destructive-command-blocker.py ~/.claude/hooks/

# Add to settings.json
claude config add hooks.pre_tool_use "python3 ~/.claude/hooks/destructive-command-blocker.py"
```

## What it blocks
- `rm -rf /` and variants
- `sudo rm`, `mkfs`, `dd` to devices
- Fork bombs, reverse shells
- `git push --force`, `git reset --hard`
- SQL `DROP TABLE`, `DELETE FROM` without WHERE
- `shutdown`, `reboot`, `kill -9 -1`
- Piping curl/wget to shell

## What it allows
- Normal file operations
- Removing temp/log files (`.log`, `.tmp`, `.pyc`)
- Non-destructive commands pass through

## Testing
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 destructive-command-blocker.py
# Output: {"decision": "block", "reason": "BLOCKED: destructive command detected (rm -rf /)"}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 destructive-command-blocker.py
# Output: {"decision": "approve"}
```

Closes #3
