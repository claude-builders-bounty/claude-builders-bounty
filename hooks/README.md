# Pre-tool-use Destructive Command Hook — Claude Code (Bounty #3, $100)

Blocks destructive bash commands before execution via a Claude Code `PreToolUse` hook.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py ~/.claude/hooks/ && python3 -c "import json,os;p=os.path.expanduser('~/.claude/settings.json');d=json.load(open(p)) if os.path.exists(p) else {};d.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/block_destructive.py'}]});json.dump(d,open(p,'w'),indent=2)"
```

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` (any flag order) | `rm -rf /`, `rm -fr x`, `sudo rm -rf /etc` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE audit;` |
| `git push --force` / `-f` | `git push --force origin main` |
| `DELETE FROM` without `WHERE` | `DELETE FROM orders;` |

Safe forms are allowed: `DELETE ... WHERE id=5`, plain `rm file.txt`,
`git push origin main`, comments/echo containing the patterns.

## Behavior

- **Exit 0** — allow (no match).
- **Exit 2** — block; Claude Code aborts the tool call. A clear explanation is
  printed and the attempt is logged.
- **Log**: `~/.claude/hooks/blocked.log` with `timestamp | reason | command | cwd`.

## Test

```bash
python3 test_block_destructive.py
```

Test suite covers all acceptance criteria: blocking patterns, logging,
allow-list behavior, and the JSON stdin protocol used by Claude Code hooks.