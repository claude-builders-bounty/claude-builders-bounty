# 🛡️ Claude Code Safety Hook

A production-quality [Claude Code](https://docs.anthropic.com/en/docs/claude-code) **PreToolUse hook** that blocks destructive bash commands before they execute — and logs every blocked attempt.

## Blocked Patterns

| Pattern | Risk | Detection Method |
|---|---|---|
| `rm -rf` / `rm -fr` / `rm --recursive --force` | Recursive forced file deletion | Token analysis (shlex) |
| `DROP TABLE` | SQL table destruction | Regex |
| `git push --force` / `git push -f` | Force push overwriting remote history | Regex |
| `TRUNCATE [TABLE]` | SQL table truncation | Regex |
| `DELETE FROM` without `WHERE` | Unconditional SQL row deletion | Regex + negative lookahead |

### What is NOT blocked (by design)

- `rm file.txt` — deletes a single file (no `-rf` flags)
- `rm -f lockfile` — force-delete a single file (no `-r`)
- `rm -r build/` — recursive without force (prompts before deleting)
- `DELETE FROM users WHERE id = 5` — has a `WHERE` clause
- `git push origin main` — normal push (no force flag)

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp /home/alan/bounty-hook/block-destructive.py /home/alan/bounty-hook/block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh ~/.claude/hooks/block-destructive.py
```

Then add the hook to your Claude Code settings. Choose one:

### Option A: Global (~/.claude/settings.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

### Option B: Per-project (.claude/settings.json)

Same JSON as above — place it in your project's `.claude/settings.json`.

## How It Works

```
Claude Code ──stdin (JSON)──▶ block-destructive.sh ──▶ block-destructive.py
                                                          │
                                                    ┌─────┴──────┐
                                                    │  check_cmd │
                                                    └─────┬──────┘
                                                          │
                                         ┌────────────────┼────────────────┐
                                         │                                │
                                   exit 0 (allow)                   exit 2 (block)
                                                                stderr = reason
                                                                log → blocked.log
```

1. Claude Code invokes the hook **before** executing any Bash tool call
2. The hook reads the tool invocation JSON from stdin (`tool_input.command`)
3. `rm` commands are parsed via `shlex.split()` for reliable flag extraction
4. SQL / git commands are matched via compiled regex patterns
5. **Safe** → exit code `0`, command proceeds
6. **Destructive** → exit code `2` + reason on stderr + log entry

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
2025-06-15T10:23:45Z | BLOCKED: rm -rf /home/user/old-data
  reason=Recursive forced deletion (rm -rf) is blocked to prevent accidental data loss.
  project=/home/user/myapp
```

Set `HOOK_BLOCKED_LOG=/custom/path.log` to override the log location.

## Testing

### Unit tests (pattern matching logic)

```bash
python3 /home/alan/bounty-hook/test_hook.py
```

### End-to-end tests (simulates Claude Code stdin)

```bash
bash /home/alan/bounty-hook/test_e2e.sh
```

### Manual smoke test

```bash
# Should block (exit 2):
echo '{"tool_input":{"command":"rm -rf /tmp/test"}}' | ~/.claude/hooks/block-destructive.sh

# Should allow (exit 0):
echo '{"tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/block-destructive.sh
```

## Files

| File | Purpose |
|---|---|
| `block-destructive.py` | Core hook logic (Python 3.8+) |
| `block-destructive.sh` | Shell wrapper (Claude Code entry point) |
| `settings.json` | Drop-in Claude Code settings snippet |
| `test_hook.py` | Unit tests for pattern matching |
| `test_e2e.sh` | End-to-end tests simulating hook invocations |
| `README.md` | This file |

## Customization

Add or remove patterns by editing `REGEX_PATTERNS` and `check_rm_pattern()` in `block-destructive.py`. Each pattern is a `(compiled_regex, reason_string)` tuple.

## License

MIT
