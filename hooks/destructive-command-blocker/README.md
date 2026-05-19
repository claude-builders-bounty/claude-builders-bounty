# 🛡️ Claude Code Destructive Command Blocker

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Category | Commands |
|----------|----------|
| **File System** | `rm -rf`, `rm -f`, `chmod 777`, `dd of=/dev/`, `mkfs`, `shred` |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` (no WHERE) |
| **Git** | `git push --force`, `git push -f`, `git reset --hard`, `git clean -fd`, `git branch -D` |
| **System** | `kill -9 1`, `sudo rm -rf /`, direct `/dev/sd` writes |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cat > ~/.claude/hooks/pre-tool-use.json << 'EOF'
{
  "hooks": {
    "Bash": [{
      "type": "command",
      "command": "python3 /path/to/pre_tool_use_hook.py"
    }]
  }
}
EOF
```

Replace `/path/to/` with the actual script location.

## How It Works

1. Claude Code sends every Bash command to the hook before execution
2. The hook checks against a curated list of destructive patterns
3. **Match found** → command is blocked, Claude sees a clear explanation
4. **No match** → command passes through normally
5. Every blocked attempt is logged to `~/.claude/hooks/blocked.log`

## Log Format

```json
{"timestamp": "2026-05-19T15:00:00", "command": "rm -rf /tmp/stuff", "reason": "rm -rf: Recursive force delete...", "project_path": "/home/user/project"}
```

## Override

To bypass the block on a specific command, add `# unsafe: allow` to the command string.

## Why This Matters

One careless `rm -rf` or `git push --force` can destroy hours of work. This hook adds a safety net that works automatically — no configuration needed, no false positives on normal commands.
