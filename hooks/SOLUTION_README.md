# Solution README — Issue #3: Pre-tool-use Security Hook

## Bounty
**[$100 USD] HOOK: Pre-tool-use hook that blocks destructive bash commands**
[Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## Solution
`pre_tool_use_bash_guard.py` — A Python hook that intercepts Claude Code's PreToolUse events for Bash commands and denies execution of destructive patterns.

## Installation

1. Copy `pre_tool_use_bash_guard.py` to `~/.claude/hooks/`:
```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use_bash_guard.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use_bash_guard.py
```

2. Configure in `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns (20+ categories)
- Recursive root deletion (`rm -rf /`, `rm -rf ~`, `rm -rf *`)
- Critical system dir deletion (`rm -rf /etc`, `/usr`, `/var`, `/home`)
- Disk formatting (`mkfs.ext4 /dev/sda1`)
- Raw disk writes (`dd if=/dev/zero of=/dev/sda`)
- Fork bombs (`:(){ :|:& };:`)
- Permission escalation (`chmod -R 777 /etc`)
- Remote pipe to shell (`curl | bash`, `wget | sh`)
- Base64 obfuscated execution (`echo ... | base64 -d | bash`)
- History clearing (`cat /dev/null > ~/.bash_history`)
- Firewall flushing (`iptables -F`, `ufw disable`)
- System file overwrite (`echo > /etc/passwd`)
- Reverse shells (`bash -i >& /dev/tcp/...`, `nc -e /bin/sh`)
- System shutdown (`shutdown`, `poweroff`, `halt`)
- Process mass kill (`killall -9 *`, `kill -9 -1`)

## Testing
```bash
pytest tests/test_solutions/test_issue_3_hook.py -v
```
35 tests covering destructive detection, safe command passing, event processing, and end-to-end CLI execution.
