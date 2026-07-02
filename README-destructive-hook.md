# Destructive Bash Command Guard — Claude Code Hook

**Bounty:** [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before execution.

## How to Install

### Step 1: Place the Hook
```bash
mkdir -p ~/.claude/hooks
cp destructive-bash-hook.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

### Step 2: Register in claude.json
Add to your `~/.claude/claude.json`:
```json
{
  "pre_tool_use_hooks": [
    {"command": "python3 ~/.claude/hooks/pre_tool_use.py"}
  ]
}
```

### Step 3: Test It
```bash
# This should be blocked:
echo 'rm -rf /' | python3 ~/.claude/hooks/pre_tool_use.py

# This should be allowed:
echo 'ls -la' | python3 ~/.claude/hooks/pre_tool_use.py
```

## What It Blocks

| Risk Level | Examples |
|---|---|
| 🔴 Critical | `rm -rf /`, `DROP DATABASE`, `mkfs.*`, `dd if=...of=/dev/*`, `iptables -F`, `shutdown -h now` |
| 🟠 High | `TRUNCATE TABLE`, `pkexec`, `chmod -R 777 /`, `DELETE FROM` (no WHERE) |
| 🟡 Medium | `UPDATE ... SET` (no WHERE), `reboot`, `killall`, crypto miner downloads |

## Configuration

The deny rules are defined at the top of the script as a list of `(regex_pattern, risk_level, reason)` tuples.

To whitelist a specific pattern, either:
- Remove the pattern from `DENY_RULES`
- Add an allow-override in your Claude config

## Logs

All blocked commands are logged to `~/.claude/hooks/blocked_commands.log`:
```
[2026-07-01T14:30:00] RISK=CRITICAL REASON="Recursive force-delete of entire filesystem" CMD=rm -rf /var/log/app
```
