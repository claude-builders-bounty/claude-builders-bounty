# Claude Code Destructive Command Blocker

A `pre-tool-use` hook for Claude Code that intercepts and aborts dangerous bash commands before execution.

## Features
- **Blocked Patterns:**
  - `rm -rf` / `rm -fr` (recursive forced deletion)
  - `git push --force` / `git push -f`
  - SQL `DROP TABLE`
  - SQL `TRUNCATE`
  - SQL `DELETE FROM <table>` when missing a `WHERE` clause
- Does **not** interfere with safe commands (e.g., `rm file.txt`, `git push origin branch`, `DELETE FROM users WHERE id = 1`).
- Logs all blocked operations to `~/.claude/hooks/blocked.log` with timestamp, project directory, and attempted command.

## Installation (2 commands)

1. Download and install the hook:
```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-command-blocker/block_destructive_commands.py -o ~/.claude/hooks/block_destructive_commands.py && chmod +x ~/.claude/hooks/block_destructive_commands.py
```

2. Register the hook in Claude Code settings:
```bash
python3 -c "import json, os; p = os.path.expanduser('~/.claude/config.json'); c = json.load(open(p)) if os.path.exists(p) else {}; c.setdefault('hooks', {})['pre-tool-use'] = ['~/.claude/hooks/block_destructive_commands.py']; json.dump(c, open(p, 'w'), indent=2)"
```