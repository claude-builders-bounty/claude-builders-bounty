# Claude Builders Bounty

A community bounty board for Claude Code builders — post tasks, claim rewards, build together.

## Available Hooks

### Destructive Command Blocker Hook (`block_destructive.py`)
Intercepts hazardous bash commands and raw SQL mutations before execution.

#### Features:
- Blocks recursive force deletions (`rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force`)
- Blocks dangerous remote git operations (`git push --force`, `git push -f`)
- Blocks database destruction (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`, unbounded `DELETE FROM` without `WHERE`)
- Logs safety violations to `~/.claude/hooks/blocked.log` with timestamp, directory path, and command.

#### Installation (2 Commands):

```bash
# 1. Install hook script
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

```bash
# 2. Configure Claude Code settings
mkdir -p ~/.claude && printf '{\n  "hooks": {\n    "PreToolUse": [\n      {\n        "matcher": "Bash",\n        "hooks": [\n          {\n            "type": "command",\n            "command": "python3 ~/.claude/hooks/block_destructive.py"\n          }\n        ]\n      }\n    ]\n  }\n}\n' > ~/.claude/settings.json
```
