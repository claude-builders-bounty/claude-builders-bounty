# pre-tool-use-block-destructive

A Claude Code `PreToolUse` hook that intercepts destructive bash commands and
blocks them before they reach the shell.

## Why

Claude Code reads your command, decides it looks reasonable, and runs it. The
margin for `rm -rf` or `DROP TABLE` is one noisy log line away from a lost
afternoon. This hook sits between Claude's intent and the shell, and refuses
to forward anything matching a known destructive pattern.

## Install (2 commands)

```bash
# 1. Drop the hook script into the hooks directory
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-block-destructive/safety_hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/safety_hook.py

# 2. Register it in ~/.claude/settings.json (one match block; idempotent)
# If you already have settings.json, merge this into the existing "hooks" object.
```

`~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [
          { "type": "command",
            "command": "~/.claude/hooks/safety_hook.py" }
        ]
      }
    ]
  }
}
```

That's the entire install. No virtualenv, no package install — the script is
stdlib-only Python 3.8+.

## Blocked patterns

| Pattern | Why blocked |
|---|---|
| `rm -rf` / `rm -r -f` / `rm -fr` | Recursive forced delete, no confirmation |
| `git push --force` / `-f` | Rewrites remote history; use `--force-with-lease` instead |
| `DROP TABLE/DATABASE/SCHEMA` | Irreversible schema destroy |
| `TRUNCATE [TABLE] x` | Removes all rows without `WHERE` |
| `DELETE FROM x` (no `WHERE`) | Would delete every row |

## Behaviour

- **Match found** → hook writes a one-line JSON record to `~/.claude/hooks/blocked.log`
  and exits with code **2**, sending a stderr message back to Claude explaining
  why the command was rejected (the upstream Claude Code client reads that
  message and refuses to run the tool).
- **No match** → hook exits with code **0** and Claude Code runs the command
  normally. The hook is invisible on the happy path.
- **`Bash` is the only gated tool.** Other tool calls (`Read`, `Write`, …)
  are not affected.

## Log format

`~/.claude/hooks/blocked.log` is append-only, one JSON object per line:

```json
{"ts": "2026-07-18T22:15:43+00:00", "project": "/home/user/proj", "command": "rm -rf build", "reason": "`rm -rf` ..."}
```

Easy to grep / pipe through `jq`:

```bash
tail -n 20 ~/.claude/hooks/blocked.log | jq .
```

## Tests

Run on any shell:

```bash
# Should echo allowed
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 hooks/pre-tool-use-block-destructive/safety_hook.py

# Should be blocked (rm -rf)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp"}' \
  | python3 hooks/pre-tool-use-block-destructive/safety_hook.py
echo "exit=$?  # 2 = blocked"
```

## License

MIT.
