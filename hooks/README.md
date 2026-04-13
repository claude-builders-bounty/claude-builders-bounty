# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before execution.

## Acceptance Criteria

✅ Hook follows Claude Code hooks format (`~/.claude/hooks/`)  
✅ Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE  
✅ Logs blocked attempts to `~/.claude/hooks/blocked.log`  
✅ Clear block message to Claude  
✅ Does not interfere with normal commands  
✅ README with 2-command install  

## Patterns Blocked

- `rm -rf /`, `rm -rf ~` — recursive force delete
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` — database destruction
- `DELETE FROM table;` (no WHERE) — unsafe deletion
- `git push --force`, `git push -f` — force push
- `iptables -F`, `ufw disable` — firewall destruction
- `dd of=/dev/sd*` — disk wipe
- Fork bomb, etc.

## Install (2 commands)

```bash
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/D2758695161/claude-builders-bounty/main/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Or copy manually:
```bash
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

Claude Code sends hook input as JSON via stdin:
```json
{"tool":"bash","args":{"command":"rm -rf /"}}
```

The hook checks the command against blocked patterns. If blocked, it returns:
```json
{"allow": false, "reason": "⛔ DESTRUCTIVE COMMAND BLOCKED..."}
```

If allowed: `{"allow": true}`

## Blocked Log

All blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Format:
```
[2026-04-13 16:00:00] BLOCKED: rm -rf / (cwd: /home/user/project)
```

## Test

```bash
echo '{"tool":"bash","args":{"command":"rm -rf /"}}' | ./pre-tool-use
# Should return: {"allow": false, ...}
```

## Bounty

Closes #3