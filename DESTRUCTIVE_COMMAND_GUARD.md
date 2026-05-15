# 🔒 Destructive Command Guard

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous Bash commands
before they can execute.

**Sponsored by Opire — $100 Bounty** | [Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## What It Blocks

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -fr` | `rm -rf /`, `rm -r -f ./src` | Irreversible file deletion |
| `DROP TABLE` | `DROP TABLE users` | Database table destruction |
| `TRUNCATE` | `TRUNCATE TABLE orders` | Mass row deletion |
| `git push --force` | `git push -f origin main` | Remote history overwrite |
| `DELETE FROM` without `WHERE` | `DELETE FROM products` | Accidental mass deletion |

Safe commands (`git push`, `rm file.txt`, `DELETE ... WHERE`) pass through unchanged.
Non-Bash tools (`Read`, `Write`, etc.) are never affected.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/destructive-command-guard.py ~/.claude/hooks/pre-tool-use/
```

That's it. Claude Code automatically picks up hooks from `~/.claude/hooks/`.

## How It Works

1. Claude Code sends a JSON payload to stdin before executing a Bash command
2. The hook checks the command against 5 regex-based block rules
3. If matched → exits 1, logs the attempt, and displays a clear message to Claude
4. If safe → exits 0, command runs normally

## Blocked Attempt Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-15T19:00:00Z]
  Rule:     rm -rf
  Command:  rm -rf /important-data
  CWD:      /home/user/project
  Reason:   Recursive forced deletion (rm -rf) can irreversibly destroy project or system files.
────────────────────────────────────────────────────────────
```

## Disabling (when you really mean it)

Run the command manually in a terminal outside Claude Code, or temporarily remove the hook:

```bash
mv ~/.claude/hooks/pre-tool-use/destructive-command-guard.py \
   ~/.claude/hooks/pre-tool-use/destructive-command-guard.py.disabled
```

## Test

```bash
# Should BLOCK these:
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}' | python3 destructive-command-guard.py
echo '{"tool_name":"Bash","tool_input":{"command":"DROP TABLE users"}}' | python3 destructive-command-guard.py
echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM products"}}' | python3 destructive-command-guard.py

# Should ALLOW these:
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 destructive-command-guard.py
echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id=1"}}' | python3 destructive-command-guard.py
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/test"}}' | python3 destructive-command-guard.py
```

## Requirements

- Python 3.7+
- Claude Code (reads hooks from `~/.claude/hooks/`)
