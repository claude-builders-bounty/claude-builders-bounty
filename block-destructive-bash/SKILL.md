---
name: block-destructive-bash
description: Use when a user wants Claude Code protected from destructive bash commands — rm -rf, force-push, DROP TABLE, TRUNCATE, unqualified DELETE, reset --hard — with logging of blocked attempts.
---

# Block Destructive Bash

Install and operate the PreToolUse hook that blocks dangerous bash commands
before Claude Code executes them.

## Install (1 command)

```bash
bash install.sh
```

Copies the hook to `~/.claude/hooks/block-destructive-bash.sh`, registers it in
`~/.claude/settings.json` under `hooks.PreToolUse` (matcher `Bash`), and is
idempotent. Claude Code must be restarted afterward.

## Verify

```bash
bash test-hook.sh    # 22 assertions; expect "22 passed, 0 failed"
```

Or probe manually:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash ~/.claude/hooks/block-destructive-bash.sh; echo "rc=$?"
# expect: BLOCKED message on stderr, rc=2
```

## Where blocks are logged

`~/.claude/hooks/blocked.log` — JSON lines, one per blocked attempt:
`{"ts": "...", "command": "...", "project": "...", "reason": "..."}`

Override the path with the `BLOCKED_LOG` environment variable.

## If a legitimate command gets blocked

The block message tells Claude it was intentional-looking-but-dangerous; the
user can run the command themselves outside Claude Code. `--force-with-lease`
is deliberately allowed as the safe alternative to `--force`.
