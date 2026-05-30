# Block Dangerous Bash Commands (Claude Code Hook)

This repo includes a `pre-tool-use` hook that blocks obviously destructive bash commands before they run.

## Installation (2 Commands)

1. Install the hook script:

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-dangerous-bash.py -o ~/.claude/hooks/block-dangerous-bash.py && chmod +x ~/.claude/hooks/block-dangerous-bash.py
```

2. Add the hook to your Claude Code settings:

```bash
python -c "import json,os,pathlib; p=pathlib.Path.home()/'.claude'/'settings.json'; p.parent.mkdir(parents=True, exist_ok=True); s=json.loads(p.read_text('utf-8')) if p.exists() else {}; h=s.get('hooks',{}); pre=h.get('pre_tool_use',[]); entry={'tool':'bash','command':['python',str(pathlib.Path.home()/'.claude'/'hooks'/'block-dangerous-bash.py')]}; pre=[x for x in pre if not (isinstance(x,dict) and x.get('command')==entry['command'] and x.get('tool')==entry['tool'])]; pre.append(entry); h['pre_tool_use']=pre; s['hooks']=h; p.write_text(json.dumps(s, indent=2, sort_keys=True)+'\\n','utf-8'); print('Updated',p)"
```

## What It Blocks

- `rm -rf`
- `git push --force` (and `-f`)
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

- `~/.claude/hooks/blocked.log`

Format (tab-separated):

`timestamp_utc<TAB>project_path<TAB>command`

