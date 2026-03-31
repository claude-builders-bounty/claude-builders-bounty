# Claude Code Pre-Tool-Use Security Hook

A security hook that intercepts and blocks dangerous bash commands before they can be executed by Claude Code.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_hook.py hook_config.json ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_hook.py
```

That's it! The hook will automatically run before each tool execution in Claude Code.

## What It Blocks

### Critical Severity (Blocked Always)
- `rm -rf /` - Root filesystem deletion
- `rm -rf ~` - Home directory deletion  
- `rm -rf *` - Wildcard deletion
- `DROP TABLE` - SQL table deletion
- `TRUNCATE TABLE` - SQL table truncation
- `dd ... of=/dev/sdX` - Direct disk writes
- `> /dev/sdX` - Redirect to disk device
- `mkfs` - Filesystem creation
- `wipefs` - Filesystem wiping
- Fork bombs (`:(){ :|:& };:`)
- `chmod 000 /` - System lockout
- `chown` on root - System corruption

### Warning Severity (Blocked)
- `DELETE FROM` (without WHERE clause) - Prevent accidental mass deletion
- `git push --force` / `git push -f` - Prevent force push accidents
- `shred` - Secure file deletion

## How It Works

1. Claude Code executes the hook before running any bash command
2. Hook checks the command against blocked patterns in `hook_config.json`
3. If matched:
   - Command is blocked (hook exits with code 1)
   - Blocked attempt is logged to `~/.claude/hooks/blocked.log`
   - User-friendly error message is shown to Claude

## Configuration

Edit `~/.claude/hooks/hook_config.json` to customize:

```json
{
  "enabled": true,
  "exit_on_block": true,
  "log_file": "~/.claude/hooks/blocked.log",
  "blocked_patterns": [
    {
      "pattern": "rm\\s+(-[rf]+\\s+)*-/",
      "description": "rm -rf / (destructive file deletion)",
      "severity": "critical"
    }
  ]
}
```

### Adding Custom Patterns

Add new patterns to `blocked_patterns`:

```json
{
  "pattern": "YOUR_REGEX_PATTERN",
  "description": "What this blocks",
  "severity": "critical"  // or "warning"
}
```

### Temporarily Disabling

Set `"enabled": false` in config to disable all blocking while keeping the hook installed.

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{
  "timestamp": "2026-03-31T09:48:00.000000",
  "command": "rm -rf /",
  "pattern": "rm\\s+(-[rf]+\\s+)*/",
  "description": "rm -rf / (destructive file deletion)",
  "severity": "critical",
  "project_path": "/home/user/project"
}
```

## Testing

Test the hook manually:

```bash
# Should be blocked (exit code 1)
echo '{"tool":"bash","arguments":{"command":"rm -rf /"}}' | python3 ~/.claude/hooks/pre_tool_hook.py
echo $?

# Should be allowed (exit code 0)
echo '{"tool":"bash","arguments":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre_tool_hook.py
echo $?
```

## Error Message Example

When a command is blocked, Claude sees:

```
🚫 SECURITY BLOCK: Command blocked by pre-tool-use hook

Reason: rm -rf / (destructive file deletion)

Attempted command: rm -rf /

This command was blocked to prevent unintended data loss or system damage.
If you intentionally want to run this command, you can:

1. Modify ~/.claude/hooks/hook_config.json to adjust blocked patterns
2. Temporarily disable the hook by setting "enabled": false in the config

Blocked attempts are logged to: ~/.claude/hooks/blocked.log
```

## Requirements

- Python 3.6+ (standard library only, no external dependencies)
- Claude Code with hooks support

## License

MIT License - Use freely for any purpose.

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.