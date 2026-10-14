# block-destructive — Claude Code PreToolUse hook

Blocks destructive Bash commands before Claude runs them: `rm -rf`,
`DROP TABLE`, `git push --force` (not `--force-with-lease`), `TRUNCATE`,
and `DELETE FROM` without `WHERE`. Everything else passes through untouched.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive.py -o ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
python3 - <<'PY'
import json,os;p=os.path.expanduser("~/.claude/settings.json");s=json.load(open(p)) if os.path.exists(p) else {}
s.setdefault("hooks",{}).setdefault("PreToolUse",[]).append({"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block-destructive.py"}]});json.dump(s,open(p,"w"),indent=2)
PY
```

## Behavior
- Blocked: exit code 2 and a message on stderr, which Claude sees.
- Each block is appended to `~/.claude/hooks/blocked.log`:
  `timestamp  project=<cwd>  command=<cmd>  reason=<why>`.

## Tests
`python3 -m unittest discover -s tests`
