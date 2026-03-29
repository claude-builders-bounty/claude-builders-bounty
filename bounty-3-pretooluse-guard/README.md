# Claude Code Guard Hook

A `PreToolUse` hook for [Claude Code](https://claude.ai/code) that intercepts and blocks destructive bash commands before they execute.

Pure bash + jq. No Python, no Node, no external dependencies.

## Install (2 commands)

```bash
git clone https://github.com/bcornish1797/claude-builders-bounty.git
bash claude-builders-bounty/bounty-3-pretooluse-guard/install.sh
```

That's it. The installer copies `guard.sh` to `~/.claude/hooks/` and adds the hook config to `~/.claude/settings.json`.

## What gets blocked

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /`, `rm -rf ./src` | Recursive force deletion |
| `DROP TABLE` | `DROP TABLE users` | Database table destruction |
| `git push --force` | `git push -f origin main` | Force push overwrites history |
| `TRUNCATE` | `TRUNCATE TABLE sessions` | Deletes all rows instantly |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Unfiltered mass deletion |

Commands that are **allowed** through:

- `rm file.txt` (no `-rf` flags)
- `rm -r dir` (no `-f`, will prompt)
- `git push origin main` (no `--force`)
- `DELETE FROM users WHERE id=5` (has WHERE clause)
- All non-Bash tools (Read, Write, Edit, etc.)

## What happens when a command is blocked

1. The command is **not executed**
2. Claude receives a message explaining why it was blocked
3. The attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
4. Claude can retry with a safer alternative

Example log entry:
```
2026-03-29T12:00:00Z | BLOCKED | project=/home/user/myapp | reason=rm -rf detected | command=rm -rf ./build
```

## Custom patterns

Add your own patterns to `~/.claude/hooks/guard-patterns.txt` (one regex per line):

```bash
# Block world-writable permissions
chmod\s+777

# Block pipe-to-shell installs
curl.*\|\s*(ba)?sh

# Block raw disk writes
dd\s+if=
```

Lines starting with `#` are comments. Empty lines are ignored.

## Configuration

| Environment variable | Default | Purpose |
|---------------------|---------|---------|
| `CLAUDE_GUARD_LOG` | `~/.claude/hooks/blocked.log` | Log file path |
| `CLAUDE_GUARD_PATTERNS` | `~/.claude/hooks/guard-patterns.txt` | Custom patterns file |

## Testing

Run the included test suite (48 test cases):

```bash
bash bounty-3-pretooluse-guard/test.sh
```

Test a specific command in dry-run mode:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash guard.sh --dry-run
# Output: [DRY-RUN] WOULD BLOCK: rm -rf detected ...
```

## Uninstall

```bash
bash install.sh --remove
```

Removes `guard.sh` from `~/.claude/hooks/` and cleans the hook entry from `settings.json`.

## How it works

The hook script receives JSON on stdin from Claude Code with the tool name and input. For Bash tool calls, it extracts the command and checks it against dangerous patterns using regex. If a match is found, it returns a JSON response with `permissionDecision: "deny"` which tells Claude Code to block the tool call and feed the reason back to Claude.

```
Claude wants to run "rm -rf /"
         │
         ▼
   guard.sh (PreToolUse hook)
         │
    Is it a Bash tool call?
         │
    ┌────┴────┐
    │ YES     │ NO → allow
    ▼         │
  Check patterns
    │
  ┌─┴──┐
  │MATCH│ NO MATCH → allow
  ▼
 Log + deny + explain to Claude
```

## Requirements

- `jq` (JSON processor) — pre-installed on most systems, or: `sudo apt install jq` / `brew install jq`
- Bash 4.0+
- Claude Code with hooks support

## License

MIT
