# 🛡️ Block Destructive Commands — Claude Code PreToolUse Hook

Intercepts dangerous bash commands **before** Claude executes them.

## What it blocks

| Command | Why |
|---------|-----|
| `rm -rf`, `rm -r -f`, `rm -fr` | Recursive force delete — can wipe the project |
| `rm --recursive --force` | Explicit recursive force delete |
| `rm --no-preserve-root` | Bypasses root protection |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM` (no WHERE) | Unconditional row deletion |
| `git push --force`, `git push -f` | Rewrites remote history |
| `chmod 777 /` | World-writable root |
| `:(){ :|:& };:` | Fork bomb |

## Install (2 commands)

```bash
# 1. Copy .claude/ folder into your project
cp -r hooks/block-destructive/.claude /path/to/your/project/

# 2. Optional: symlink for global use
mkdir -p ~/.claude/hooks
ln -sf $(pwd)/hooks/block-destructive/block-destructive.sh ~/.claude/hooks/block-destructive.sh
```

**Requires:** `jq` (`brew install jq` / `apt install jq`)

## How it works

Claude Code sends the Bash command as JSON on stdin. The hook:
1. Parses `tool_input.command` with jq
2. Checks against destructive patterns (case-insensitive)
3. **Denies** matching commands via `hookSpecificOutput`
4. **Logs** to `~/.claude/hooks/blocked.log`
5. **Allows** safe commands through

## Log format

```
[2026-05-11T17:00:00Z] BLOCKED | reason=Recursive force delete | command=rm -rf /tmp | project=/home/user
```
