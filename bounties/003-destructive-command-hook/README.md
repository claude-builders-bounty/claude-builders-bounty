# Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

**2 commands:**

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/block-destructive.py https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/bounties/003-destructive-command-hook/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
```

```bash
cat > ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "bash",
        "hook": "~/.claude/hooks/block-destructive.py"
      }
    ]
  }
}
EOF
```

## What It Blocks

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` | `rm -rf /path` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users` | Database destruction |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Mass data deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Mass deletion |
| `git push --force` | `git push -f origin main` | Rewrites history |
| `git reset --hard` | `git reset --hard HEAD~5` | Loses uncommitted work |
| `dd of=/dev/` | `dd if=img.iso of=/dev/sda` | Overwrites disk |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Formats filesystem |

## How It Works

1. **Intercepts** every bash command before execution
2. **Pattern matches** against known dangerous operations
3. **Blocks** the command with a clear error message
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log`
5. **Allows** safe commands to proceed normally

## Log Format

Every blocked attempt is logged with:

```
[2026-06-27T18:30:45.123456] BLOCKED: rm -rf (recursive force delete)
  Command: rm -rf /tmp/test
  Project: /home/user/project
  ============================================================
```

## Testing

```bash
# These will be blocked:
rm -rf /tmp/test
git push --force origin main
echo "DROP TABLE users;" | sqlite3 db.sqlite

# These will pass:
rm /tmp/test
git push origin main
echo "SELECT * FROM users;" | sqlite3 db.sqlite
```

## Bypassing the Block

If you really need to run a blocked command:

1. **Temporarily disable the hook:**
   ```bash
   # Edit ~/.claude/settings.json and remove the hook
   ```

2. **Or run the command directly in your terminal** (hooks only apply to Claude Code)

## Customization

Edit `DANGEROUS_PATTERNS` in `block-destructive.py` to add/remove patterns:

```python
DANGEROUS_PATTERNS = [
    (r'\byour_pattern\b', 'description'),
    # Add more patterns here
]
```

## Requirements

- Python 3.7+ (pre-installed on most systems)
- Claude Code with hooks support

## License

MIT
