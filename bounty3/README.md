# Destructive command PreToolUse hook (Claude Code)

**Bounty:** [claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100 via Opire  
**Status:** local artifact ready; GitHub PAT lacks `repo` create/fork/gist — cannot open PR until token scopes expanded.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/".claude"/"settings.json"
cfg = json.loads(p.read_text()) if p.exists() else {}
hooks = cfg.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
  "matcher": "Bash",
  "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive.py"}]
}
if entry not in pre:
    pre.append(entry)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(cfg, indent=2))
print("updated", p)
PY
```

## Acceptance mapping

| Criterion | Implementation |
|-----------|----------------|
| Claude Code hooks format | `PreToolUse` command hook |
| Blocks recursive force remove, DROP TABLE, force push, TRUNCATE, DELETE w/o WHERE | `RULES` regexes in hook |
| Logs blocked attempts | `~/.claude/hooks/blocked.log` |
| Clear message to Claude | stderr + JSON `decision:block` |
| Safe commands pass | unit tests |
| README ≤2 install commands | above |

## Test

```bash
python3 tests/test_hook.py
```

## Claim path (blocked by token)

1. `/opire try` on issue #3  
2. Fork + PR with this tree  
3. Payment on merge via Opire/Stripe  
