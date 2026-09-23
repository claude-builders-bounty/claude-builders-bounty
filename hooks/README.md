# Destructive Bash PreToolUse Hook

A dependency-free Claude Code `PreToolUse` hook that blocks dangerous Bash commands before execution.

## What it blocks

- `rm -rf` / equivalent combined recursive+force flags
- `DROP TABLE`
- `git push --force`, `--force-with-lease`, `--force-if-includes`, and `-f`
- `TRUNCATE`
- `DELETE FROM` statements with no `WHERE` clause

Every blocked attempt is appended as JSONL to `~/.claude/hooks/blocked.log` with UTC timestamp, attempted command, project path, and reason. Safe commands exit normally without output.

## Install — 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/'.claude'/'settings.json'; p.parent.mkdir(parents=True, exist_ok=True)
d = json.loads(p.read_text()) if p.exists() and p.read_text().strip() else {}
h = d.setdefault('hooks', {}).setdefault('PreToolUse', [])
h.append({'matcher':'Bash','hooks':[{'type':'command','command':'~/.claude/hooks/block_destructive.py'}]})
p.write_text(json.dumps(d, indent=2) + '\n')
PY
```

## Hook behavior

Claude Code sends the hook event as JSON on stdin. If the command is blocked, the hook returns a `hookSpecificOutput` object with `hookEventName: PreToolUse`, `permissionDecision: deny`, and a clear reason. If the command is safe, it exits `0` without interfering.

## Tests

```bash
cd hooks && python3 -m unittest -v test_block_destructive.py
```

The tests cover all required destructive patterns, normal commands, safe `DELETE ... WHERE ...`, and a multi-statement SQL case where a `WHERE` in one statement must not mask a destructive delete in another.


## Verification (2026-09-23)

Fresh validation against this submitted branch on Windows/Python 3.12:

```text
python hooks/test_block_destructive.py
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```

GitHub comparison also reported this branch mergeable and 0 commits behind the current base when checked. AI assistance was used; the test result above was actually executed, and does not assert merge, acceptance, or payment.
