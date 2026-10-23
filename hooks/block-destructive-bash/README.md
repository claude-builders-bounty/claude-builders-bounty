# Claude Code Pre-Tool-Use Hook: Destructive Bash Blocker

Intercepts and blocks dangerous bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause) before execution, logging every blocked attempt to `~/.claude/hooks/blocked.log`.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py && chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
python3 -c "import json,os;p=os.path.expanduser('~/.claude/settings.json');os.makedirs(os.path.dirname(p),exist_ok=True);d=json.load(open(p)) if os.path.exists(p) else {};d.setdefault('hooks',{})['PreToolUse']=[{'matcher':'Bash','hooks':[{'type':'command','command':'~/.claude/hooks/pre_tool_use_blocker.py'}]}];json.dump(d,open(p,'w'),indent=2)"
```

## What Gets Blocked & Logged
- `rm -rf` / `rm -fr`
- `DROP TABLE` / `DROP DATABASE`
- `TRUNCATE`
- `git push --force` / `git push -f`
- `DELETE FROM <table>` without a `WHERE` clause
- Logs timestamp, attempted command, and project path to `~/.claude/hooks/blocked.log`.
