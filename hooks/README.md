# Claude Code Destroy Hook 🛡️

A `pre-tool-use` hook for Claude Code that intercepts and blocks destructive bash commands before they execute.

## What it blocks

| Pattern | Example |
|---------|---------|
| Recursive delete of root/parent | `rm -rf /`, `rm -rf ..` |
| Disk wipe | `dd if=/dev/zero of=/dev/sda` |
| Filesystem format | `mkfs.ext4 /dev/sdb1` |
| Partition deletion | `fdisk /dev/sda delete` |
| SQL truncate | `TRUNCATE TABLE users` |
| SQL drop | `DROP TABLE users; DROP DATABASE prod` |
| SQL delete without WHERE | `DELETE FROM users;` (no WHERE) |
| Force git push | `git push --force`, `git push -f` |
| Fork bomb | `:(){:|:&};:` |

## Installation

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy this hook
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use

# 3. Enable in CLAUDE.md or .clauderc
{
  "hooks": {
    "pre-tool-use": "~/.claude/hooks/pre-tool-use"
  }
}
```

Or add to your `~/.clauderc.json`:

```json
{
  "hooks": {
    "pre-tool-use": {
      "command": "python3",
      "args": ["~/.claude/hooks/pre-tool-use"]
    }
  }
}
```

## What gets logged

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-27 10:30:15] BLOCKED: rm -rf /home/user/prod | Reason: Recursive delete of root or parent | Project: /home/user/projects/api
```

## Testing

```bash
# Test blocking (should be blocked, exits 1)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 pre-tool-use
echo $?  # Should print 1

# Test allowing (should pass, exits 0)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 pre-tool-use
echo $?  # Should print 0

# Test non-Bash tools (always allowed)
echo '{"tool_name":"Read","tool_input":{"file_path":"/etc/passwd"}}' | python3 pre-tool-use
echo $?  # Should print 0
```

## Usage Notes

- Requires Python 3.6+
- Works with Claude Code's hook system
- Only intercepts `Bash` tool calls
- Other tools (Read, Write, Edit, etc.) pass through unaffected
- If you need to run a blocked command, run it directly in your terminal

## Files

- `pre-tool-use` — the hook script (Python 3)
- `blocked.log` — auto-created on first blocked command
