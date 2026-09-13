# Safeguard — PreToolUse hook that blocks destructive bash

**Bounty:** [#3 — $100](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)  
**Author:** KvngJamesII

Intercepts Claude Code Bash tool calls and **denies** before execution when the command matches:

| Pattern | Behavior |
|---------|----------|
| `rm -rf` / `rm -fr` | deny + log |
| `DROP TABLE` | deny + log |
| `TRUNCATE` | deny + log |
| `git push --force` / `-f` / `--force-with-lease` | deny + log |
| `DELETE FROM …` **without** `WHERE` | deny + log |

Every block appends to `~/.claude/hooks/blocked.log`:

```
2026-09-13T20:15:00Z | rm -rf /tmp/x | /path/to/project
```

Uses the current Claude Code hook schema (`hookSpecificOutput.permissionDecision: deny`).

## Install (2 commands)

```bash
# 1) copy hook
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py

# 2) merge into Claude settings (creates file if missing)
python3 -c "import json,pathlib;p=pathlib.Path.home()/'.claude'/'settings.json';d=json.loads(p.read_text()) if p.exists() else {};d.setdefault('hooks',{}).setdefault('PreToolUse',[]);frag=json.load(open('hooks/settings.fragment.json'))['hooks']['PreToolUse'][0];d['hooks']['PreToolUse']=[x for x in d['hooks']['PreToolUse'] if 'block_destructive' not in str(x)]+[frag];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2));print('updated',p)"
```

Restart Claude Code / start a new session.

## Test without Claude

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/proj"}' \
  | python3 hooks/block_destructive.py
# → JSON deny + line in ~/.claude/hooks/blocked.log

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 hooks/block_destructive.py
# → empty (allows normal commands)
```

Or run `python3 tests/test_block_destructive.py`.

## Design notes

- Dedicated DELETE-FROM parser (not a naïve regex) so `DELETE FROM t WHERE id=1` still works
- Blocks `--force-with-lease` too (same class of history rewrite)
- Never matches non-Bash tools — zero interference with Read/Edit/Write
