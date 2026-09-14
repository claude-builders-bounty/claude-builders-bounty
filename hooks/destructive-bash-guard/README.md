# Claude Code Pre-Tool-Use Guard Hook

A lightweight, zero-dependency Python security hook for Claude Code that blocks dangerous and destructive shell commands before they execute.

## Blocked Patterns
- `rm -rf` (and all recursive force removal variations)
- `DROP TABLE` (SQL statements)
- `git push --force` (including `-f` and `--force-with-lease`)
- `TRUNCATE` (SQL table truncations)
- `DELETE FROM` without a `WHERE` clause

All blocked attempts are recorded with a UTC timestamp, attempted command, and project path in `~/.claude/hooks/blocked.log`. Safe commands (including `git push origin main`, `rm file.txt`, and `DELETE FROM ... WHERE ...`) continue without interference.

---

## Complete Installation (2 commands)

Install the hook file and automatically register it in `~/.claude/settings.json` in two commands:

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/pre-tool-use.py
python3 ~/.claude/hooks/pre-tool-use.py --install
```

*On Windows (PowerShell):*
```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\hooks"; Copy-Item block_destructive_bash.py "$HOME\.claude\hooks\pre-tool-use.py"
python "$HOME\.claude\hooks\pre-tool-use.py" --install
```

After running these 2 commands, the hook is fully installed and active.

---

## Configuration Reference

The `--install` command automatically manages your `~/.claude/settings.json` (preserving all existing settings and hooks):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/pre-tool-use.py"
      }
    ]
  }
}
```

When a destructive command is intercepted, the hook returns a structured `deny` decision to Claude Code:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

---

## Verification & Testing

Run the built-in test suite to verify all rules, installer idempotency, and Claude Code protocol compliance:

```bash
python test_hook.py
```
