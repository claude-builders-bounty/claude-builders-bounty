# 🛡️ Pre-tool-use Guard — Block Destructive Bash Commands

A Claude Code **pre-tool-use hook** that intercepts and blocks dangerous bash commands before they execute. Prevents accidental data loss from `rm -rf`, SQL destruction, force pushes, and more.

## Blocked Patterns

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /`, `rm -rf ./build` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | SQL table deletion |
| `git push --force` | `git push --force origin main` | Force push overwrites history |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | SQL mass data wipe |
| `DELETE FROM` (no `WHERE`) | `DELETE FROM users;` | Unbounded SQL delete |

Safe commands pass through without interference. For example, `rm file.txt`, `git push origin main`, and `DELETE FROM users WHERE id = 5` are all allowed.

## Installation

```bash
git clone https://github.com/YPC0813/claude-builders-bounty.git && bash claude-builders-bounty/hooks/pre-tool-use-guard/install.sh
```

That's it — **one command**. The installer:

1. Copies `guard.py` to `~/.claude/hooks/`
2. Registers the hook in `~/.claude/settings.json`

### Requirements

- Python 3.10+
- [`jq`](https://jqlang.github.io/jq/) (for the installer to merge settings)

### Manual Installation

If you prefer to install manually:

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks
cp guard.py ~/.claude/hooks/guard.py
chmod +x ~/.claude/hooks/guard.py

# 2. Add to ~/.claude/settings.json
```

Add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/guard.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

```
Claude decides to run a Bash command
        │
        ▼
  ┌─────────────┐
  │ PreToolUse   │  Claude Code fires the hook event
  │ event fires  │
  └──────┬───────┘
         │
         ▼
  ┌─────────────┐
  │ guard.py     │  Reads JSON from stdin, extracts the command
  │ inspects cmd │
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
 blocked    safe
    │         │
    ▼         ▼
  deny      exit 0
  + log     (allow)
```

1. Claude Code fires a `PreToolUse` event for every Bash tool call
2. `guard.py` reads the JSON input from stdin
3. The command is checked against destructive patterns (regex-based)
4. **Blocked**: Returns a `deny` decision with a clear explanation; logs to `~/.claude/hooks/blocked.log`
5. **Safe**: Exits with code 0 (allow) — no output, no delay

### Block Log

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-21T03:00:00Z] BLOCKED
  Pattern : rm -rf (recursive force delete)
  Command : rm -rf /tmp/important-data
  Project : /home/user/my-project
────────────────────────────────────────────────────────
```

## Testing

```bash
python3 test_guard.py
```

Or with pytest:

```bash
python3 -m pytest test_guard.py -v
```

## Uninstall

```bash
rm ~/.claude/hooks/guard.py
```

Then remove the `PreToolUse` hook entry from `~/.claude/settings.json`.

## License

MIT — see [LICENSE](../../LICENSE)
