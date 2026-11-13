# Block Destructive Bash Commands — Claude Code PreToolUse Hook

A `PreToolUse` hook for Claude Code that intercepts dangerous bash commands
**before** they run, and denies them with a clear explanation — while letting
normal commands through untouched.

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` / `rm -fr` / `rm -r -f` / `--recursive --force` (incl. `sudo rm -rf`) | Irreversibly deletes whole directory trees |
| `DROP TABLE` | Permanently deletes a table and all its data |
| `git push --force` / `git push -f` | Overwrites remote history (use `--force-with-lease` instead — allowed) |
| `TRUNCATE` | Deletes every row of a table |
| `DELETE FROM` without `WHERE` | Deletes every row of a table |

## What it allows (no false positives)

`ls`, `git status`, `git push origin main`, `git push --force-with-lease`,
`rm file.txt`, `rm -r dir`, `rm -f file`, `DELETE FROM users WHERE id=1`,
`echo "rm -rf /"`, `grep -rf …` — all pass through silently.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a
UTC timestamp, the project path, and the attempted command:

```
2026-11-13T00:22:03+00:00 | cwd=/tmp/testproj | command=rm -rf /tmp/foo
```

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.py
python3 -c "import json,os; p=os.path.expanduser('~/.claude/settings.json'); s=json.load(open(p)) if os.path.exists(p) else {}; s.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/block-destructive.py'}]}); json.dump(s,open(p,'w'),indent=2)"
```

That is it — no dependencies beyond Python 3 (standard library only).

## Test it

```bash
echo 'rm -rf /tmp/foo' | python3 ~/.claude/hooks/block-destructive.py
# -> {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}

echo 'ls -la' | python3 ~/.claude/hooks/block-destructive.py
# -> (no output, exit 0: allowed)
```

The test suite covering 37 cases (all blocked patterns + normal commands)
passes 37/37 — see `test_hook.py`.
