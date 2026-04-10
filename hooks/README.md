# Pre-Tool-Use Hook: Block Destructive Bash Commands

**Bounty:** [$100 — claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)  
**Stack:** Python 3.7+ (no external dependencies)

---

## What It Does

A Claude Code `pre-tool-use` hook written in Python that intercepts `Bash` tool calls and blocks dangerous commands before they execute. Every blocked attempt is logged with timestamp, command, and project path.

## Installation (2 commands)

```bash
# 1. Copy the hook into your Claude hooks directory
mkdir -p ~/.claude/hooks
cp pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use-blocker.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use-blocker.py
```

Claude Code auto-discovers hooks in `~/.claude/hooks/` by filename convention. The file is named `pre-tool-use-blocker.py` so it is registered as a `pre-tool-use` hook (run before each tool call).

## Blocked Patterns

| Pattern | Why |
|---|---|
| `rm -rf /` | Wipes root filesystem |
| `rm -rf .` | Deletes project files irreversibly |
| `mv ... /dev/null` | Silently destroys data |
| `> /etc/...` | Overwrites system config |
| `git push --force` / `-f` | Overwrites shared remote history |
| `DROP TABLE` | Deletes an entire database table |
| `DROP DATABASE` | Deletes an entire database |
| `TRUNCATE` | Deletes all rows from a table |
| `DELETE FROM table;` (no WHERE) | Deletes every row |
| `history -c` | Erases your shell history |

## Log File

Every blocked attempt is appended to:

```
~/.claude/hooks/blocked.log
```

Example entry:
```
[2026-04-10T06:44:00+00:00] BLOCKED command in /home/user/my-project: 'rm -rf .'
  Reason: recursive delete of current directory
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Allow the tool call |
| `33` | Block the tool call |
| other | Allow (fail-open) |

Fail-open means malformed input or hook errors never block Claude.

## Test It

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"project_path":"/test"}' \
  | python3 ~/.claude/hooks/pre-tool-use-blocker.py
echo "exit code: $?"   # should be 33
cat ~/.claude/hooks/blocked.log
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use-blocker.py
```

## Extending

Add patterns to the `DANGEROUS_PATTERNS` list in `pre-tool-use-blocker.py`:

```python
(r'your_pattern\s+',  "human-readable reason"),
```

Re-copy to `~/.claude/hooks/` — no restart needed.
