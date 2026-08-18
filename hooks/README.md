# Pre-Tool-Use Safety Hook

A Claude Code `PreToolUse` hook that detects and blocks destructive bash
commands before they execute.

## Purpose

This hook inspects every Bash tool invocation and blocks commands that match
known-destructive patterns.  It is a **safety net**, not a shell sandbox — it
cannot prevent all forms of data loss.

## Installation

Copy the hook into your Claude Code hooks directory and make it executable:

```bash
cp pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
```

That's it — Claude Code will invoke it automatically for every tool call.

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` (any order of flags containing r and f) | `rm -rf /`, `rm -fr ./data`, `rm -r -f /tmp/x` |
| `DROP TABLE` | `DROP TABLE users` |
| `git push --force` (but NOT `--force-with-lease`) | `git push --force origin main` |
| `git push -f` | `git push -f origin main` |
| `TRUNCATE` / `TRUNCATE TABLE` | `TRUNCATE TABLE logs` |
| `DELETE FROM` without a `WHERE` clause | `DELETE FROM users` |

## Allowed Examples

- `rm file.txt` — single file removal is fine.
- `git push origin main` — normal push.
- `DELETE FROM users WHERE id = 1` — targeted delete.
- `git push --force-with-lease origin main` — safe force variant.
- `echo "I need to truncate this string"` — harmless text.
- Any non-Bash tool event (e.g. Read, Write, WebSearch).

## Log Location

Blocked attempts are appended to:

```
~/.claude/hooks/blocked.log
```

Each entry contains an ISO-8601 timestamp, the attempted command, and the
project path (if available).

## How It Works

1. Claude Code sends a JSON event to the hook via stdin.
2. The hook checks whether the event is a Bash tool invocation.
3. If Bash, the command string is matched against destructive patterns.
4. On match: the hook exits 2, prints a JSON deny response with a reason,
   and logs the attempt.
5. On no match (or non-Bash): the hook exits 0 and allows the tool call.

## Example Outputs

**Safe command (allowed):**
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
```

**Destructive command (blocked):**
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "rm with -rf (recursive force delete) is blocked"}}
```
