## 💰 Bounty: $100 — powered by [Opire](https://opire.dev)

## What

Pre-tool-use hook that intercepts and blocks destructive bash commands before Claude Code executes them.

## Deliverables

- `hooks/pre-tool-use/block-destructive.py` — Python implementation
- `hooks/pre-tool-use/block-destructive.sh` — Bash implementation
- `hooks/pre-tool-use/README.md` — Installation guide (2 commands)

## Acceptance Criteria Met

- ✅ Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- ✅ Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`, plus 15+ more patterns
- ✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log` with: timestamp, attempted command, project path
- ✅ Displays clear message to Claude explaining why the command was blocked
- ✅ Does not interfere with normal bash commands (exits silently for safe commands)
- ✅ README with installation in 2 commands or fewer

## Blocked Patterns (20+)

`rm -rf`, `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE`, `git push --force`/`-f`, `git reset --hard`, `git clean -df`, `chmod -R 777`, `chown -R`, `mkfs`, `dd to device`, `> /dev/sd*`, fork bomb, `shutdown`, `reboot`, `halt`, `killall`, `pkill -9`

## Installation

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use/block-destructive.py ~/.claude/hooks/pre-tool-use.py
```

Then add to `~/.claude/settings.json`:
```json
{"hooks":{"pre-tool-use":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/pre-tool-use.py"}]}]}}
```

/opire try

Closes #3
