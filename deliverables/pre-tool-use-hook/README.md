# Pre-Tool-Use Hook — Claude Code

> Intercepts and blocks dangerous bash commands before they are executed.

---

## Quick Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use-hook && chmod +x ~/.claude/hooks/pre-tool-use-hook
```

Or for Python version:

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_hook.py ~/.claude/hooks/pre-tool-use-hook && chmod +x ~/.claude/hooks/pre-tool-use-hook
```

---

## What It Blocks

| Category | Patterns |
|----------|----------|
| **File Destruction** | `rm -rf`, `rm -fr`, `rmdir -f`, `mv */dev/null`, `: >`, `> file` (truncate) |
| **Database Destruction** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM table` (no WHERE) |
| **Git Destruction** | `git push --force`, `git push -f`, `git reset --hard`, `git clean -fdx` |
| **System Destruction** | `mkfs`, `dd if=... of=/dev/`, `fdisk`, `parted`, `shutdown`, `reboot`, `poweroff` |
| **Kernel Modules** | `rmmod`, `insmod`, `modprobe` |
| **Package Removal** | `apt-get remove`, `apt-get purge`, `yum remove`, `dnf remove`, `brew uninstall`, `pip uninstall`, `npm uninstall` |

---

## How It Works

1. **Hooks into Claude Code** — placed in `~/.claude/hooks/pre-tool-use-hook`
2. **Intercepts every bash command** — before the tool executes
3. **Matches against 30+ dangerous patterns** — regex-based detection
4. **Blocks and logs** — writes to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
5. **Shows clear message** — explains why the command was blocked and what to do

---

## Log Format

```
[2026-05-24T06:57:00Z] BLOCKED | Pattern: Destructive: rm -rf | Command: rm -rf /tmp/data | Path: /home/user/project
```

---

## Bypass

If you intentionally need to run a blocked command, use the `--force` flag:

```bash
claude --force "rm -rf /tmp/old-cache"
```

---

## Testing

```bash
# Should be blocked
bash pre-tool-use-hook.sh "rm -rf /tmp/data"
echo $?  # → 1 (blocked)

# Should pass
bash pre-tool-use-hook.sh "ls -la"
echo $?  # → 0 (allowed)

# Should be blocked
bash pre-tool-use-hook.sh "git push --force origin main"
echo $?  # → 1 (blocked)

# Should pass
bash pre-tool-use-hook.sh "git push origin main"
echo $?  # → 0 (allowed)
```

---

## Files

| File | Language | Description |
|------|----------|-------------|
| `pre-tool-use-hook.sh` | Bash | Standalone bash hook (no dependencies) |
| `pre_tool_use_hook.py` | Python | Python hook with richer pattern matching |

---

## Claude Code Hooks Docs

- [Official Documentation](https://docs.anthropic.com/claude-code/hooks)

---

## Bounty

**$100** — [claude-builders-bounty/claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
