# 🛡️ Block Destructive Commands — Claude Code Hook

A pre-tool-use hook for **Claude Code** that prevents accidental execution of destructive shell commands.

**Bounty:** [Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100

---

## What It Blocks

| Pattern | Example |
|---|---|
| `rm -rf` / `rm -fr` / `rm --recursive --force` | `rm -rf /project/data` |
| `DROP TABLE` (SQL) | `DROP TABLE users;` |
| `git push --force` / `git push -f` | `git push origin main --force` |
| `TRUNCATE` (SQL) | `TRUNCATE TABLE logs;` |
| `DELETE FROM` **without** `WHERE` (SQL) | `DELETE FROM users;` ✅ *but `DELETE FROM users WHERE id=1;` passes* |

## How It Works

When Claude Code is about to run a command, this hook intercepts it, checks it against the destructive patterns above, and either:

- ✅ **Allows** the command (exits with code 0) — safe commands pass through instantly
- ❌ **Blocks** the command (exits with code 1) — displays a clear message and logs the attempt

All blocked commands are logged to `blocked.log` with:
- Timestamp (UTC ISO 8601)
- The full command
- The reason it was blocked
- Project path

## 2-Step Install

### Step 1 — Create the hooks directory

```bash
mkdir -p ~/.claude/hooks
```

### Step 2 — Copy the hook & make it executable

```bash
cp hooks/block-destructive/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

> **Note:** The filename must be exactly `pre-tool-use` (no extension) and must be executable.

## Verification

```bash
# Check the hook is installed
ls -la ~/.claude/hooks/pre-tool-use

# Test it (should block)
echo '{"name":"Bash","input":{"command":"rm -rf /tmp"}}' | python3 ~/.claude/hooks/pre-tool-use
echo $?  # should be 1

# Test safe command (should allow)
echo '{"name":"Bash","input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre-tool-use
echo $?  # should be 0

# Check the log
cat ~/.claude/hooks/blocked.log
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Files

| File | Purpose |
|---|---|
| `pre-tool-use` | Executable hook script (Python 3) |
| `README.md` | This file |
| `blocked.log` | Auto-created log of blocked commands |

## How It's Different from `git push --force-with-lease`

`git push --force` overwrites remote branches unconditionally. `--force-with-lease` is safer (checks if your remote ref matches what you expect) and is **NOT blocked** by this hook.
