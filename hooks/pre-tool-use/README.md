# Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/* ~/.claude/hooks/pre-tool-use/
```

Or, install directly from this repo:

```bash
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/block-destructive-commands.py -o ~/.claude/hooks/pre-tool-use/block-destructive-commands.py && chmod +x ~/.claude/hooks/pre-tool-use/block-destructive-commands.py
```

## Blocked Commands

| Category | Pattern | Reason |
|---|---|---|
| Filesystem | `rm -rf /`, `rm -rf ~`, `rm -rf $HOME` | Root/home directory deletion |
| Filesystem | `:(){ :\|:& };:` | Fork bomb |
| Filesystem | `> /dev/sda`, `dd if=... of=/dev/...` | Raw block device overwrite |
| Filesystem | `mkfs.*` | Filesystem format |
| Database | `DROP TABLE`, `DROP DATABASE` | Table/database deletion |
| Database | `TRUNCATE [TABLE]` | Table truncation |
| Database | `DELETE FROM <table>` (without WHERE) | Unconditional delete |
| Git | `git push --force main/master` | Force push to protected branch |
| Git | `git push -f main/master` | Force push to protected branch |
| Git | `git reset --hard` | Hard reset |
| Git | `git clean -fdx` | Remove all untracked files |
| System | `chmod -R 777 /` | World-writable root |
| System | `chown -R ... /` | Ownership change on root |
| System | `shutdown`, `reboot`, `halt` | System power commands |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{"timestamp": "2026-09-05T12:00:00Z", "command": "rm -rf /tmp/bad", "project": "/home/user/project"}
```

## How It Works

1. Claude Code calls the hook before executing any Bash tool command
2. The hook checks the command against a list of destructive patterns
3. If a pattern matches, the command is blocked and Claude sees an explanation
4. Normal commands pass through without interference

## Testing

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 hooks/pre-tool-use/block-destructive-commands.py
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre-tool-use/block-destructive-commands.py
```

## Override

To intentionally run a blocked command, temporarily move the hook:
```bash
mv ~/.claude/hooks/pre-tool-use/block-destructive-commands.py ~/.claude/hooks/pre-tool-use/block-destructive-commands.py.bak
# ... run your command ...
mv ~/.claude/hooks/pre-tool-use/block-destructive-commands.py.bak ~/.claude/hooks/pre-tool-use/block-destructive-commands.py
```
