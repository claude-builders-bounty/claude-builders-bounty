# 🛡️ Destructive Command Guard — Claude Code Hook

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that **blocks dangerous commands** before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre_tool_use
ln -sf "$PWD/block.sh" ~/.claude/hooks/pre_tool_use/block.sh
```

That's it. Relaunch Claude Code — the hook is active.

## How It Works

Claude Code calls `pre_tool_use` hooks **before** every bash command. This hook:

1. Reads the JSON payload from stdin (Claude Code hooks protocol)
2. Checks the command against 20 destructive patterns
3. **Blocks** the command with a clear explanation
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log`
5. Allows all other commands to pass normally

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` | Permanent recursive deletion |
| `rm -rf /` / `rm -r /` | Root filesystem destruction |
| `DROP TABLE` / `DROP DATABASE` | Irreversible database drops |
| `TRUNCATE` (bare) | Mass row deletion |
| `git push --force` / `git push -f` | Force-push overwrites history |
| `DELETE FROM` (no WHERE) | Mass row deletion |
| `> /dev/sda` | Raw disk writes |
| `mkfs.` | Filesystem formatting |
| `:(){ :\|:& };:` | Fork bombs |
| `chmod 000 /` | OS-breaking permissions |
| `chown -R 0:0 /` | Dangerous ownership change |
| `mv /* /dev/null` | File destruction |

## Logs

Every blocked attempt is logged with:
- Timestamp
- The pattern matched
- The full command
- The working directory

```text
~/.claude/hooks/blocked.log
```

## What It Doesn't Block

✅ `rm file.txt` (targeted delete)  
✅ `rm -r temp/` (with explicit path, not root)  
✅ `git push --force-with-lease` (safe force push)  
✅ `DELETE FROM users WHERE id = 1` (has WHERE clause)  
✅ `DROP TABLE IF EXISTS temp_backup` (safe drop in migration)  
✅ All normal development commands

## Requirements

- Python 3 (stdlib only — no pip packages required)
- Bash

Works on macOS, Linux, WSL.

## Testing

```bash
# Verify the hook works without Claude Code
echo '{"command": ["rm", "-rf", "/tmp/test"]}' | python3 hook.py
# → {"allowed": false, "reason": "..."}

echo '{"command": ["ls", "-la"]}' | python3 hook.py
# → {"allowed": true}
```

## File Structure

```
├── block.sh    ← Bash entry point (symlinked to ~/.claude/hooks/)
├── hook.py     ← Python logic (called by block.sh)
└── README.md   ← This file
```
