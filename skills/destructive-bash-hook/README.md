# claude-guard-hook

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before they run.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/anlogrian-rgb/claude-guard-hook/main/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

```bash
python3 - <<'EOF'
import json,os
p=os.path.expanduser("~/.claude/settings.json")
d=json.load(open(p)) if os.path.exists(p) else {}
h=d.setdefault("hooks",{}).setdefault("PreToolUse",[])
entry={"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/pre-tool-use.py"}]}
if entry not in h: h.append(entry)
json.dump(d,open(p,"w"),indent=2)
print("hook registered in", p)
EOF
```

## Blocked patterns

| Pattern | Severity |
|---|---|
| `rm -rf` (recursive/forced delete) | CRITICAL |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | CRITICAL |
| `TRUNCATE` | CRITICAL |
| `git push --force` / `-f` / `--force-with-lease` | CRITICAL |
| `DELETE FROM` **without** `WHERE` | CRITICAL |

Safe commands pass through untouched (`git push origin main`, `DELETE FROM x WHERE id=5`, `rm notes.txt`, `npm test`, `ls`).

## Behaviour

- Reads hook JSON on stdin: `{"tool_name":"Bash","tool_input":{"command":"..."},"cwd":"..."}`
- Exit `0` = allow, exit `2` = block (message shown to Claude).
- Every block is logged to `~/.claude/hooks/blocked.log` as one JSON line:
  `{"timestamp","command","pattern","severity","project_path"}`

## Test

```bash
echo '{"tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/proj"}' | ./pre-tool-use.py; echo "exit=$?"
echo '{"tool_input":{"command":"ls -la"},"cwd":"/proj"}' | ./pre-tool-use.py; echo "exit=$?"
```

Expected: first prints a BLOCKED message and exits `2`; second exits `0`.

## License

MIT
