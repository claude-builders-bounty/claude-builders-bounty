# Claude Code Dangerous Command Blocker

A **pre-tool-use hook** for [Claude Code](https://code.claude.com) that blocks dangerous Bash commands before they execute. Designed for the [Claude Builders Bounty](https://opire.dev) challenge (issue #3).

## Features

- Blocks **five categories** of dangerous commands:
  - `rm -rf` (recursive forced deletion)
  - `DROP TABLE` (SQL table destruction)
  - `git push --force` / `git push -f` (force push)
  - `TRUNCATE [TABLE]` (SQL table truncation)
  - `DELETE FROM` **without** `WHERE` (SQL mass deletion)
- **Logs every blocked attempt** to `~/.claude/hooks/blocked.log` with:
  - Timestamp (ISO 8601)
  - The full command that was blocked
  - The working directory at the time
- Follows the official [Claude Code Hooks format](https://code.claude.com/docs/en/hooks).
- Uses the `permissionDecision: "deny"` response so Claude understands why the command was blocked.

## Installation

### 1. Place the hook script

```bash
# Copy the script into your global hooks directory
cp blocker.sh ~/.claude/hooks/blocker.sh
chmod +x ~/.claude/hooks/blocker.sh
```

### 2. Configure Claude Code to use the hook

Add the following to **either** `~/.claude/settings.json` (global, all projects) **or** `.claude/settings.json` (per-project, shareable via git):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$HOME/.claude/hooks/blocker.sh\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

> **Note:** `"matcher": "Bash"` ensures the hook only fires on Bash tool calls, avoiding unnecessary overhead on Read/Write/Edit tool calls.

### 3. Verify installation

Run `/hooks` inside a Claude Code session to confirm the hook is loaded:

```
/hooks
```

You should see a `PreToolUse` hook registered with a `Bash` matcher pointing to `blocker.sh`.

## How It Works

1. When Claude Code calls the **Bash** tool, the `PreToolUse` event fires.
2. The matcher `"Bash"` activates this hook group.
3. Claude Code passes the tool call as JSON on **stdin** (includes `tool_name`, `tool_input.command`, `cwd`, etc.).
4. `blocker.sh` reads stdin, extracts the command, and checks it against five dangerous patterns.
5. **If dangerous:** logs to `blocked.log` and outputs a `permissionDecision: "deny"` JSON response → Claude Code blocks the command and informs Claude.
6. **If safe:** exits with code 0 and no stdout → the command proceeds normally.

### Input format (received on stdin)

```json
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /tmp/build"
  },
  "tool_use_id": "toolu_01ABC123"
}
```

### Output format (to block a command)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked by security hook: dangerous command detected"
  }
}
```

## Dangerous Patterns Detected

| Pattern | Example | Risk |
|---|---|---|
| `rm -rf` | `rm -rf /` | Recursive forced file deletion |
| `DROP TABLE` | `DROP TABLE users;` | Destructive SQL schema change |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `git push -f` | `git push -f` | Overwrites remote history (short form) |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Destructive SQL data removal |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unconditional SQL row deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM "orders";` | Quoted table names, still dangerous |

### What is NOT blocked

- `rm file.txt` (singular file, no `-rf` flags)
- `DELETE FROM table WHERE id = 1` (has `WHERE` clause)
- Normal git operations: `git push`, `git push origin main`, `git commit`, etc.
- SQL `INSERT`, `UPDATE`, `SELECT` statements
- `DROP` used in non-SQL contexts (e.g., `drop table-migration.sql`)

## Log File Format

Blocked attempts are appended to **`~/.claude/hooks/blocked.log`** in this format:

```
[2026-05-08 03:30:00] BLOCKED | cmd=rm -rf /tmp/build | cwd=/home/user/my-project
[2026-05-08 03:35:12] BLOCKED | cmd=DROP TABLE users | cwd=/home/user/my-project
[2026-05-08 03:40:33] BLOCKED | cmd=git push --force origin main | cwd=/home/user/my-project
```

Each line contains:
- **Timestamp** in `YYYY-MM-DD HH:MM:SS` format
- **cmd**: The full command that was blocked
- **cwd**: The working directory at the time of the attempt

## Requirements

- `jq` — for JSON parsing (almost always present on systems running Claude Code)

To install `jq` if missing:

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Fedora/RHEL
sudo dnf install jq
```

## Files

| File | Purpose |
|---|---|
| `blocker.sh` | The hook script — reads JSON from stdin, detects dangerous commands, logs and blocks them |
| `~/.claude/hooks/blocked.log` | Log file for blocked attempts (auto-created) |
| `~/.claude/settings.json` | Claude Code settings that register the hook (user must edit) |

## License

MIT — See the [Claude Builders Bounty](https://opire.dev) repository for details.
