# block-destructive-bash — a Claude Code PreToolUse hook

Stops Claude Code from running the handful of bash commands that destroy things before
you notice.

**Blocks** `rm -rf` / `rm -fr` / `rm -r -f` · `DROP TABLE` · `TRUNCATE` ·
`DELETE FROM` with no `WHERE` · `git push --force`
**Allows** everything else, plus `git push --force-with-lease` (which is safe) and any
command tagged `guard:allow`
**Logs** every block to `~/.claude/hooks/blocked.log` — timestamp, project path, command, reason

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude/settings.json"
p.parent.mkdir(parents=True, exist_ok=True)
s = json.loads(p.read_text()) if p.exists() else {}
s.setdefault("hooks", {}).setdefault("PreToolUse", []).append(
    {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive.py"}]})
p.write_text(json.dumps(s, indent=2))
print("registered")
PY
```

On Windows use `python` instead of `python3`. Manual alternative: merge
`settings.snippet.json` into `~/.claude/settings.json` yourself.

## What Claude sees when it's blocked

```
BLOCKED by destructive-bash guard
  reason : `rm` with recursive + force — deletes silently, no undo
  command: rm -rf node_modules
  project: ~/code/app
  logged : ~/.claude/hooks/blocked.log
Re-run the same command to proceed anyway, or tag it with `guard:allow` to skip the guard.
```

Exit code 2 tells Claude Code to stop and adjust — so Claude gets the reason and can choose
to override or fix the command.

## Override

- Let Claude re-run it and confirm — the block is advisory, not a wall.
- Or tag the command: `rm -rf node_modules # guard:allow`.

## What it will not do

- It is a denylist, not a linter. `rm -rf` is blocked even when it's harmless (which is the
  point — the blast radius is what matters, not the intent).
- SQL keywords are only matched in bare SQL or inside a real runner (`psql`, `mysql`,
  `sqlite3`, …), so `git commit -m "DROP TABLE fix"` doesn't trip it.
- The log grows unbounded; rotate it if you like.

## Tests

```
python test_hook.py
```

28 cases — 14 must block (exit 2), 14 must pass (exit 0) — plus a check that every block
writes a log line with timestamp, project path and command.

## Uninstall

Remove the `PreToolUse` entry from `~/.claude/settings.json` and delete
`~/.claude/hooks/block_destructive.py`.
