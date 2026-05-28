# 🛡️ Claude Code Safety Hook

A pre-tool-use hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks destructive bash commands before they execute.

**Bounty:** [#3 — $100](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force-delete can destroy files irreversibly |
| `DROP TABLE` | Permanently deletes a database table |
| `git push --force` | Overwrites remote history (suggests `--force-with-lease`) |
| `TRUNCATE` | Removes all rows without row-level logging |
| `DELETE FROM` (no WHERE) | Deletes ALL rows from a table |

## Installation (2 commands)

```bash
git clone https://github.com/RomuloGatto/claude-builders-bounty.git
bash claude-builders-bounty/safety-hook/install.sh
```

Or install directly:

```bash
curl -fsSL https://raw.githubusercontent.com/RomuloGatto/claude-builders-bounty/main/safety-hook/install.sh | bash
```

## How It Works

1. Claude Code calls the hook before each `Bash` tool invocation
2. The hook reads the command from stdin (JSON format)
3. If a dangerous pattern is detected:
   - The command is **blocked** (exit code 2)
   - A clear message is shown to Claude explaining why
   - The attempt is logged to `~/.claude/hooks/blocked.log`
4. Safe commands pass through unaffected (exit code 0)

## Blocked Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-28T03:15:00Z] BLOCKED | project: /home/user/myapp | command: rm -rf /tmp/data | reason: Blocked: 'rm -rf' is a recursive force-delete...
```

## Uninstall

```bash
rm ~/.claude/hooks/safety-hook.sh
```

## Accepted Stack

Bash — no external dependencies beyond `python3` (for JSON parsing, available on all modern systems).

## License

MIT
