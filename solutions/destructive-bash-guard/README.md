# PreToolUse hook: block destructive bash commands

A dependency-free `guard.sh` hook for Claude Code that inspects every `Bash` tool call
and **blocks** (exit 2) patterns that are catastrophic, irreversible, or exfiltrative,
while leaving normal development commands alone. Every blocked attempt is appended to
`~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp guard.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/guard.sh
```

Then add the hook to `~/.claude/settings.json` (merge with any existing `hooks` block):

```bash
jq '.hooks.PreToolUse = [{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/guard.sh"}]}]' ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

Restart the session. Test with `rm -rf ~` (blocked, logged) and `ls -la` (allowed).

## What it blocks

| Class | Examples |
|---|---|
| Filesystem destruction | `rm -rf /`, `rm -rf ~`, `rm -rf ..`, `> /dev/sda`, `mkfs.*`, fork-bombs |
| Database destruction | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without a WHERE clause |
| Remote code exec | `curl … \| sh`, `wget … \| bash` |
| Repo damage | force-push to main/master, bare `git reset --hard`, `git clean -fd` |
| Host damage | `shutdown`/`reboot`, stopping system services, `chmod -R 777`, mass-kill |
| Secret exfiltration | curls touching `~/.ssh/id_*`, `.aws/credentials`, `/etc/shadow`, `.env` |

When a command is blocked, Claude sees a stderr message explaining exactly why (e.g.
`BLOCKED by safety hook: DROP TABLE destroys data irreversibly`) and the attempt is
logged to `~/.claude/hooks/blocked.log` as:

```
2026-08-01T12:34:56Z	/home/user/myproject	psql -c 'DROP TABLE users;'
```

Text-processing one-liners (`grep`, `sed`, `echo`, …) containing SQL keywords inside
quoted arguments are not treated as database commands, so prose like
`grep -i 'drop table' notes.md` is allowed.

Allow-list philosophy beats block-list philosophy for prod boxes, but block-lists win
for a general dev agent: near-zero false positives on everyday commands, and the exact
failure mode observed in the wild (an agent `rm -rf`ing outside its workspace) is covered.

## Testing

See `test-hook.sh`: feeds 50+ JSON events through the hook and asserts allow/block,
plus verifies the blocked.log format. Run it with:

```bash
bash test-hook.sh
```

It exits non-zero on any regression.
