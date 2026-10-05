# block-destructive-commands.sh

Claude Code `PreToolUse` hook — intercepts dangerous bash commands **before**
they execute and blocks them with an explanation.

Blocked patterns:
- `rm -rf` variants (`-fr`, `-r -f`, `--recursive --force`, `sudo rm -rf …`)
- `DROP TABLE`, `TRUNCATE`
- `git push --force` / `git push -f` (`--force-with-lease` is allowed — it's the safe variant)
- `DELETE FROM …` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as
`timestamp | project path | attempted command`.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive-commands.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-commands.sh
```

```bash
python3 - <<'EOF'
import json, os
p = os.path.expanduser('~/.claude/settings.json')
d = json.load(open(p)) if os.path.exists(p) else {}
d.setdefault('hooks', {}).setdefault('PreToolUse', []).append(
    {"matcher": "Bash", "hooks": [{"type": "command",
     "command": os.path.expanduser("~/.claude/hooks/block-destructive-commands.sh")}]})
json.dump(d, open(p, 'w'), indent=2)
print("hook registered")
EOF
```

## Test

```bash
bash test_hook.sh   # 35 real-execution tests
```

## Protocol

Block verdict is returned as (current Claude Code format, with legacy fallback):

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"…"},"decision":"block","reason":"…"}
```

## Design notes

- **Conservative matching**: the hook errs on the side of blocking (e.g. `echo rm -rf /`
  is blocked too). For a safety hook, a false positive costs a sentence of explanation;
  a false negative costs data.
- **Best-effort, not a sandbox**: determined obfuscation (`r\m`, `$'rm'`, unicode tricks)
  can bypass any regex. This hook stops accidents and the obvious attacks, which is what
  the bounty asks for.
- **Fail-open on bad input**: malformed hook JSON exits 0 silently so a broken hook
  never bricks Claude Code.
- Matching is case-insensitive; pure-bash (python3 used only for JSON parsing when
  available, with a sed fallback).
