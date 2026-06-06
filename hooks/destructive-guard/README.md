# destructive-guard

A Claude Code `PreToolUse` hook that blocks irreversible bash commands before they execute.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` (any flag order) | `rm -rf /`, `rm -fr .`, `rm -r -f /build` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM logs;` |
| `git push --force` / `-f` | `git push --force origin main` |

Safe variants are allowed: `rm -f file.txt`, `git push --force-with-lease`, `DELETE FROM … WHERE id=1`.

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/destructive-guard/install.sh
```

That's it. The hook copies itself to `~/.claude/hooks/` and registers in `~/.claude/settings.json`.

## How it works

Claude Code calls the hook before every `Bash` tool use. The hook reads JSON from stdin:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
```

If the command matches a blocked pattern, it writes:

```json
{"decision": "block", "reason": "rm -rf: recursive force-delete is irreversible"}
```

Blocked attempts are logged as JSON lines to `~/.claude/hooks/blocked.log`.

## Tests

```bash
cd hooks/destructive-guard
pytest tests.py -v   # 33 tests, all patterns covered
```
