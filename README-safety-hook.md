# Safety Hook — Block Destructive Bash Commands in Claude Code

> **[Bounty #3]** A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

---

## Install (2 commands)

```bash
# 1. Copy the hook to Claude Code's hooks directory
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre_tool_use.py
```

That's it. The hook is active immediately — no restart needed.

---

## What it blocks

| Pattern | Why it's dangerous |
|---------|-------------------|
| `rm -rf` (any variant) | Permanently deletes files — no recycle bin |
| `DROP TABLE` | Irreversible database table deletion |
| `TRUNCATE` | Deletes all rows with no WHERE clause |
| `DELETE FROM` without `WHERE` | Wipes every row in a table |
| `git push --force` / `-f` / `--force-with-lease` | Rewrites remote history |
| Writing to `/etc/passwd`, `/etc/shadow`, etc. | Overwrites critical system files |
| `chmod 777` on system directories | Removes all permission restrictions |

---

## How it works

Claude Code calls the hook with tool input on `stdin` as JSON. The hook:

1. Parses the JSON to extract the `command` field (only for `Bash` tool calls)
2. Checks against a list of dangerous regex patterns
3. If matched:
   - Logs the attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
   - Prints a clear explanation to Claude explaining what was blocked and why
   - Exits with code `2` (Claude Code's signal to block the tool call)
4. If safe: exits with code `0` (allow)

---

## Log format

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-07-02T08:20:00+00:00] BLOCKED
  Command: 'rm -rf /important/data'
  Reason:  Recursive force-remove (rm -rf): could permanently delete critical files
  Project: /home/user/my-project
  ---
```

---

## Requirements

- Python 3.8+
- Claude Code with hooks support

No third-party dependencies.

---

## Testing

```bash
# Test: should be blocked
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | python3 pre_tool_use.py
echo "Exit code: $?"

# Test: should be allowed
echo '{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}' | python3 pre_tool_use.py
echo "Exit code: $?"

# Test: should be blocked
echo '{"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}' | python3 pre_tool_use.py
echo "Exit code: $?"
```

Expected exit codes: `2` (blocked), `0` (allowed), `2` (blocked)

---

## Configuration

To add or modify blocked patterns, edit `pre_tool_use.py` — the `BLOCKED_PATTERNS` list at the top of the file. Each entry is a `(regex, description)` tuple.
