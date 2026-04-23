# Destructive Command Blocker

A Claude Code pre-tool-use hook that prevents execution of dangerous bash commands that could cause irreversible data loss.

## Installation

```bash
# Copy hook to Claude Code hooks directory
cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
```

That's it! The hook is now active for all Claude Code sessions.

## What It Blocks

### File Deletion
- `rm -rf /` - Recursive force deletion
- `rm -rf *` - Wildcard deletions
- `rm -rf <any-path>` - Any recursive force deletion

### SQL Destructive Operations
- `DROP TABLE users` - Table deletion
- `TRUNCATE TABLE logs` - Table truncation
- `DELETE FROM users;` - Deletion without WHERE clause

### Git Force Operations
- `git push --force` - Force push
- `git push -f` - Force push (short form)

### System-Level Dangerous Operations
- `mkfs.*` - Filesystem formatting
- `dd if=... of=/dev/...` - Direct disk writes
- Fork bombs

## How It Works

1. **Pre-execution Check**: Intercepts bash commands before Claude Code executes them
2. **Pattern Matching**: Compares command against known dangerous patterns
3. **Blocking**: If dangerous pattern detected, prevents execution and shows clear error
4. **Logging**: Records all blocked attempts to `~/.claude/hooks/blocked.log`
5. **Pass-through**: Safe commands execute normally with zero overhead

## Example: Blocked Command

When Claude tries to run `rm -rf node_modules/`:

```
🚫 COMMAND BLOCKED: Dangerous file deletion (rm -rf)

The following command was blocked because it could cause irreversible data loss:

    rm -rf node_modules/

This command was logged to: ~/.claude/hooks/blocked.log

If you need to run this command, please:
1. Review the command carefully
2. Ensure you have backups
3. Run it manually outside of Claude Code

Alternatively, consider a safer approach to accomplish your goal.
```

## Log Format

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-23 15:30:42] BLOCKED: Git force push
  Command: git push --force origin main
  Project: /Users/you/projects/important-app
--------------------------------------------------------------------------------
[2026-04-23 15:31:15] BLOCKED: SQL deletion without WHERE clause
  Command: DELETE FROM users;
  Project: /Users/you/projects/database-app
--------------------------------------------------------------------------------
```

## Safe Commands Pass Through

These commands execute normally (not blocked):

```bash
rm file.txt                    # Single file deletion
rm -r old-folder              # Recursive without force
git push origin main          # Normal push
DELETE FROM users WHERE id=5  # SQL with WHERE clause
```

## Technical Details

- **Language**: Python 3.7+
- **Hook Type**: `pre-tool-use` (runs before tool execution)
- **Exit Codes**:
  - `0` - Command allowed, proceed with execution
  - `1` - Command blocked, do not execute
- **Performance**: ~1ms overhead per bash command (negligible)

## Customization

To add more dangerous patterns, edit `pre-tool-use.py`:

```python
DANGEROUS_PATTERNS = [
    (r'your-pattern-here', 'Reason why dangerous'),
    # ... existing patterns ...
]
```

Pattern format: `(regex_pattern, human_readable_reason)`

## Uninstallation

```bash
rm ~/.claude/hooks/pre-tool-use.py
```

## Requirements

- Claude Code with hooks support
- Python 3.7+ (already available in Claude Code environment)
- Write permissions to `~/.claude/hooks/`

## License

MIT

## Credits

Built for the Claude Builders Bounty Program
