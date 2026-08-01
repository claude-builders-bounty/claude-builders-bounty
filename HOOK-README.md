# block-destructive-commands

> A Claude Code `PreToolUse` hook that blocks dangerous bash commands before they execute.

Catches and blocks: `rm -rf`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`, and `git push --force`. Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Why

Claude Code is powerful, but power + haste = disaster. This hook is a safety net for the moments when an LLM hallucinates a destructive command and tries to run it.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/block-destructive-commands.py https://raw.githubusercontent.com/TriggerXZ/block-destructive-commands/main/block-destructive-commands.py && chmod +x ~/.claude/hooks/block-destructive-commands.py
```

Then add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
          }
        ]
      }
    ]
  }
}
```

Done. Next time Claude Code tries to run a dangerous command, it will be blocked with a clear explanation.

## What gets blocked

| Pattern | Reason shown to Claude |
|---|---|
| `rm -rf` (any variant) | "recursive force delete (rm -rf)" |
| `DROP TABLE` | "DROP TABLE" |
| `TRUNCATE [TABLE] foo` | "TRUNCATE" |
| `DELETE FROM foo` (no WHERE) | "DELETE FROM without WHERE clause" |
| `git push --force` | "git push --force" |
| `git push -f` | "git push --force" |
| `git push --force-with-lease` | "git push --force-with-lease" |

## What does NOT get blocked

Normal commands pass through unchanged. Examples that are allowed:

- `rm file.txt` (no `-rf`)
- `DELETE FROM users WHERE id = 5` (has WHERE)
- `git push origin main` (no `--force`)
- `git push --force-with-lease` is BLOCKED (safer alternative still risky)

## Log format

Every block is appended to `~/.claude/hooks/blocked.log`:

```
[2026-08-01T12:45:32] project=/home/user/myproject | reason=rm -rf | command=rm -rf node_modules
[2026-08-01T12:51:14] project=/home/user/api | reason=DROP TABLE | command=psql -c "DROP TABLE users;"
```

The log never grows unbounded by default — rotate or `truncate` it as needed.

## How it works

Claude Code invokes the hook before any `Bash` tool call. The hook:

1. Reads the proposed command from stdin (JSON).
2. Runs regex matches against the block list.
3. If matched: logs the attempt, prints `{"decision": "block", "reason": "..."}` to stdout.
4. If not matched: prints `{"decision": "allow"}` and the command runs normally.

## Files

- `block-destructive-commands.py` — the hook (Python 3, zero external dependencies)
- `settings.example.json` — drop-in snippet for `~/.claude/settings.json`
- `test.sh` — 12 unit tests for the block patterns

## Testing

```bash
bash test.sh
```

The test suite covers all 5 required patterns plus edge cases (e.g. `rm --recursive --force`, `DELETE FROM x WHERE y=1` should be allowed).

## Compatibility

- ✅ Linux, macOS
- ✅ Windows (Git Bash, WSL) — Python 3 required
- ✅ Claude Code 1.0+
- ✅ No external dependencies (stdlib only)

## License

MIT — see [LICENSE](./LICENSE).
