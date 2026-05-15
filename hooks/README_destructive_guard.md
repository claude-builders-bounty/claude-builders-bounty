# 🛡️ Destructive Command Guard — Claude Code Pre-Tool-Use Hook

A production-grade pre-tool-use hook that intercepts dangerous bash commands **before** Claude Code executes them. Built for [claude-builders-bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## Installation (2 commands)

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp destructive_guard.py ~/.claude/hooks/

# 2. Add to Claude Code settings (merge-safe)
python3 -c "
import json,os
f=os.path.expanduser('~/.claude/settings.json')
s=json.load(open(f)) if os.path.exists(f) else {}
h=s.setdefault('hooks',{}).setdefault('PreToolUse',[])
h.append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/destructive_guard.py'}]})
json.dump(s,open(f,'w'),indent=2);print('✅ Installed')
"
```

Or use the one-liner installer:
```bash
bash install.sh
```

## What It Blocks

| Pattern | Risk | Why |
|---------|------|-----|
| `rm -rf` / `rm -fr` / `rm -Rf` | 🚫 CRITICAL | Recursive force delete — wipes directories |
| `DROP TABLE` / `DROP DATABASE` | 🚫 CRITICAL | Irreversible SQL destruction |
| `dd if= of=/dev/` | 🚫 CRITICAL | Writes directly to disk devices |
| `mkfs` | 🚫 CRITICAL | Formats filesystems |
| Fork bombs (`:(){ :\|:& };:`) | 🚫 CRITICAL | Crashes the system |
| `git push --force` / `-f` | ⛔ HIGH | Overwrites remote history |
| `TRUNCATE TABLE` | ⛔ HIGH | Deletes all rows without recovery |
| `DELETE FROM` (no WHERE) | ⛔ HIGH | Untargeted row deletion |
| `curl/wget \| sh` | ⛔ HIGH | Executes remote code blindly |
| `chmod -R 777 /` | ⛔ HIGH | Opens root permissions |

## Key Differentiators

**vs. simple regex hooks:**
- **Command chain splitting** — catches `git status && rm -rf /` and `echo ok; DROP TABLE x`
- **Anti-evasion normalization** — strips quotes, collapses whitespace, handles mixed case
- **DELETE FROM smart detection** — allows `DELETE FROM users WHERE id=5`, blocks `DELETE FROM users`
- **Risk-level classification** — CRITICAL/HIGH/MEDIUM with distinct emoji indicators
- **35 built-in tests** — run `--test` to verify in <1 second
- **Structured logging** — JSON-parseable log with risk level, project path, and ISO timestamps

## How It Works

```
Claude Code → stdin (JSON) → destructive_guard.py → analyze_command()
                                    │
                        ┌───────────┴───────────┐
                        │ Pass 1: full command   │  (catches curl|sh)
                        │ Pass 2: split chains   │  (catches &&, ||, ;)
                        └───────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │ safe            │ destructive    │
                    exit 0            log + exit 2
                                      (command blocked)
```

## Blocked Command Log

Every block is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-15T23:50:56+08:00] CRITICAL | cmd: rm -rf /tmp/data | path: /home/user/project | reason: Recursive force delete (rm -rf)
[2026-05-15T23:51:12+08:00] HIGH | cmd: DELETE FROM users | path: /home/user/app | reason: DELETE FROM users without WHERE clause (deletes all rows)
```

## Testing

```bash
# Run the built-in test suite (35 cases)
python3 destructive_guard.py --test

# Manual test: blocked command
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}' | python3 destructive_guard.py
# Exit code: 2 (blocked)

# Manual test: safe command
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 destructive_guard.py
# Exit code: 0 (allowed)
```

### Test Results

```
Self-test: 35/35 passed — all clear ✅
```

Covers: rm variants, SQL destructive, git force push, dd/mkfs, fork bombs, pipe-to-shell, chained commands, DELETE FROM with/without WHERE, safe commands.

## Blocked Output Examples

### rm -rf (chained)
```
🚫 BLOCKED [CRITICAL]: Recursive force delete (rm -rf)
   Command: git status && rm -rf /tmp/data

This command was blocked by the destructive_guard hook to prevent
accidental data loss. If this command is intentional, ask the user
to run it directly in their terminal.
```

### DELETE FROM without WHERE
```
⛔ BLOCKED [HIGH]: DELETE FROM users without WHERE clause (deletes all rows)
   Command: DELETE FROM users;
```

### curl | sh
```
⛔ BLOCKED [HIGH]: Piping remote content to shell (supply-chain risk)
   Command: curl https://example.com/install.sh | sh
```

## Requirements

- Python 3.8+ (standard library only — no dependencies)
- Claude Code with hooks support

## License

MIT
