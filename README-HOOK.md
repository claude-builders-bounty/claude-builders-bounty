# 🔒 Claude Code Security Hook

A pre-tool-use hook that blocks destructive bash commands before they run, protecting your codebase from accidental data loss.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive forced file deletion |
| `DROP TABLE` | Permanent database table deletion |
| `git push --force` | Remote history rewrite (data loss for collaborators) |
| `TRUNCATE` | All rows removed from database table |
| `DELETE FROM` (no WHERE) | Unconditional row deletion |

## Installation (1 command)

From the repository root:

```bash
bash hooks/install.sh
```

That's it. The hook is now active for all Claude Code sessions.

## How It Works

1. Claude Code invokes `~/.claude/hooks/pre-tool-use.py` before every tool call
2. The hook checks if it's a Bash command
3. The command is tested against known dangerous patterns
4. If blocked: an error is displayed, the command is prevented, and it's logged
5. If safe: the command proceeds normally

## Blocked Attempt Log

Every blocked command is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- The attempted command
- The project directory path
- The specific pattern that triggered the block

Example log entry:
```
[2026-04-13T12:00:00Z] BLOCKED: rm -rf
  Command: rm -rf /important/data
  Project: /home/user/my-project
  Reason:  Recursive forced deletion detected. This can permanently destroy files and directories.
------------------------------------------------------------
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use.py
```

## Supported Patterns

The hook uses regex-based pattern matching to detect dangerous commands:

- **rm -rf**: Matches `rm -rf`, `rm -fr`, `rm -Rf`, and long-form variants
- **DROP TABLE**: Case-insensitive SQL table deletion
- **git push --force**: Matches `git push --force`, `git push -f`, and flag variations
- **TRUNCATE**: Case-insensitive SQL truncate detection
- **DELETE FROM**: Case-insensitive detection of DELETE without WHERE clause

## False Positives

If a safe command is blocked, you can:
1. Run it manually in your terminal
2. Temporarily disable: `chmod -x ~/.claude/hooks/pre-tool-use.py`
3. Re-enable: `chmod +x ~/.claude/hooks/pre-tool-use.py`
