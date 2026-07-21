# Destructive Command Blocker — Claude Code Hook

A `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## What It Blocks

| Category | Patterns Blocked |
|----------|------------------|
| **Filesystem** | `rm -rf /`, `rm -rf ~`, `rm -rf *`, `rm -rf ..`, writes to `/dev/sd*` |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git** | `git push --force` (without `--lease`), `git push -f`, `git reset --hard`, `git clean -f` |
| **Permissions** | `chmod 777 /`, `chmod 777 ~`, `chmod -R 777`, `chown -R root` |
| **RCE Vectors** | `curl ... | sh`, `wget ... | sh`, `bash -c $(...)` |
| **System** | Fork bombs (`:(){ :|:& };:`), `dd of=/dev/`, `mkfs`, `fdisk` |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

## Test It

```bash
# This will be blocked with explanation
rm -rf /tmp/test

# This proceeds normally
echo "safe command"
```

## Logs

Blocked attempts logged to `~/.claude/hooks/blocked.log`:

```
[2026-07-19T14:32:15Z] BLOCKED | project=/home/user/myapp | command="rm -rf /" | reason="rm -rf on root directory — irreversible system destruction"
```

## How It Works

1. Claude Code runs `bash` tool → passes JSON to hook stdin
2. Hook parses command, checks against 20+ regex patterns
3. If dangerous: returns `{"decision": "block", "reason": "..."}` + logs
4. If safe: returns `{"decision": "proceed"}`
5. Claude shows reason to user, command never executes

## Customization

Edit `DANGEROUS_PATTERNS` list in `pre_tool_use.py` to add/remove patterns.

## Requirements

- Python 3.8+ (standard on all systems)
- No external dependencies

---

**Bounty**: Issue #3 — $100 via Opire  
**Author**: kabbersokhi-boop