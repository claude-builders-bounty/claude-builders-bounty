# 🛡️ Bash Guard — Claude Code Pre-Tool-Use Hook

A safety hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before they execute.

## Blocked Patterns

| Pattern | Severity | Why |
|---------|----------|-----|
| `rm -rf` | 🔴 Critical | Recursive force delete |
| `DROP TABLE` / `DROP DATABASE` | 🔴 Critical | Permanent data loss |
| `TRUNCATE` | 🔴 Critical | Unlogged bulk delete |
| `DELETE FROM` (no WHERE) | 🔴 Critical | Deletes all rows |
| `git push --force` | 🟡 Warning | Overwrites remote history |
| `git reset --hard` (main/master) | 🔴 Critical | Destroys branch history |
| `chmod 777` | 🟡 Warning | Overly permissive |
| `curl \| sh` | 🟡 Warning | Executes untrusted code |
| `mkfs` / `dd of=/dev/` | 🔴 Critical | Formats/overwrites disk |
| Fork bomb | 🔴 Critical | Crashes system |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use_guard.py ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "preToolUse": [{
      "matcher": "Bash",
      "command": "python3 ~/.claude/hooks/pre_tool_use_guard.py"
    }]
  }
}
```

That's it. The hook now runs automatically before every bash command Claude Code attempts.

## How It Works

1. Claude Code calls the hook before executing any `Bash` tool
2. The hook reads the command from stdin (JSON)
3. Checks against 15 destructive patterns (regex-based)
4. If matched: logs to `~/.claude/hooks/blocked.log` and returns exit code 2 (block)
5. If safe: returns exit code 0 (allow)

## Logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-02 10:30:00 UTC] [CRITICAL] BLOCKED
  Command: rm -rf /tmp/project
  Project: /home/user/my-app
  Reason:  Recursive force delete (rm -rf) — can destroy entire directories
────────────────────────────────────────────────────────────────
```

## Design Decisions

- **Fail-open for non-Bash tools** — only intercepts the `Bash` tool, all other tools pass through
- **Fail-open on parse errors** — if stdin can't be parsed, allows execution (won't break Claude Code)
- **Regex-based patterns** — catches variants like `rm -fr`, `rm -Rf`, etc.
- **`--force-with-lease` allowed** — `git push --force-with-lease` is safe (checks remote state)
- **`DELETE FROM ... WHERE` allowed** — only blocks DELETE without WHERE clause
- **Non-interactive** — no prompts, no TTY required, pure stdin/stdout

## Customization

Edit the `DESTRUCTIVE_PATTERNS` list in the script to add/remove patterns. Each entry is:

```python
(
    re.compile(r"your_regex_here"),
    "Human-readable reason for blocking",
    "critical"  # or "warning"
)
```

## License

MIT
