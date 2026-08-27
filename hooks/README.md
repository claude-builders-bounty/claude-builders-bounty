# claude-code-safety-hook

A Claude Code `PreToolUse` hook that blocks destructive bash commands
before they execute. Pure Python, zero third-party dependencies, ~150 lines.

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` outside `/tmp` and `/var/tmp` | Recursive force-delete of the wrong path is the #1 cause of "I just lost my repo" moments |
| `mkfs` | Formats a filesystem |
| `dd of=/dev/sd*` (or `nvme`, `vd`, `mmcblk`) | Writes directly to a block device |
| `> /dev/sd*` | Same, via shell redirect |
| `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` | Irreversible DDL |
| `TRUNCATE` | Wipes a table without WHERE |
| `DELETE FROM` without `WHERE` | Full-table delete |
| `git push --force` / `-f` / `--force-with-lease` | Rewrites remote history; other devs lose commits |

## Install (2 commands)

```bash
# 1. Drop the hook into your Claude hooks directory
curl -fsSL https://raw.githubusercontent.com/tronnew/claude-builders-bounty/main/hooks/safety_hook.py -o ~/.claude/hooks/safety_hook.py && chmod +x ~/.claude/hooks/safety_hook.py

# 2. Wire it up in your Claude settings (merge with existing hooks if needed)
curl -fsSL https://raw.githubusercontent.com/tronnew/claude-builders-bounty/main/hooks/settings.example.json -o ~/.claude/settings.json
```

Restart Claude Code. That's it.

## Configuration (env vars)

| Variable | Default | Effect |
|---|---|---|
| `SAFETY_HOOK_BLOCKED_LOG` | `~/.claude/hooks/blocked.log` | Where blocked attempts are appended |
| `SAFETY_HOOK_ALLOW_PATH_PREFIX` | `/tmp,/var/tmp` (for `rm -rf` only) | Comma-separated path prefixes that may be `rm -rf`'d |
| `SAFETY_HOOK_DRY_RUN` | unset | When `1`, log only — never block. Useful to audit rules before enforcement. |

## How blocking works

Claude Code runs the configured command with the pending tool call as
JSON on stdin. If the command exits with code `2`, Claude treats the
tool call as blocked and surfaces the stderr message back to itself. Any
other exit code allows the call. This hook:

- Returns `0` (allow) for non-Bash tool calls or unrecognized input.
- Returns `2` (block) when a rule fires, and writes a clear message to
  stderr explaining which rule tripped and how to bypass it if
  intentional.
- Fails OPEN on internal errors: if the hook itself crashes, the
  command is allowed (with a stderr warning) rather than blocking
  every operation. This is the safer default for a safety net — a
  misconfigured hook should not brick your session.

## Log format

`~/.claude/hooks/blocked.log` is a tab-separated file:

```
2026-08-27T13:45:02+00:00\t/home/user/project\tDROP TABLE / DROP DATABASE / DROP SCHEMA\tDROP TABLE users;
```

Columns: ISO-8601 UTC timestamp, project path, rule name, command. Easy
to ingest into any log pipeline or `awk` over.

## Testing

```bash
# Should exit 2 and log:
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /home/me"}}' | python3 safety_hook.py; echo $?

# Should exit 0:
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}' | python3 safety_hook.py; echo $?

# Should exit 0:
echo '{"tool_name":"Read","tool_input":{"path":"/etc/passwd"}}' | python3 safety_hook.py; echo $?
```

## Limitations

- Heuristic, not bulletproof. An attacker (or tired-you) can always
  find a way to phrase a destructive command that the regex misses.
  Pair this hook with code review and backups.
- Only intercepts Bash commands. File edits via the Edit/Write tools
  can still overwrite files — those don't go through this hook.
- `rm -rf /tmp/anything` is allowed by default. If your `/tmp` is
  actually a symlink into your home directory, you're on your own.
