# Security Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/geldbert/claude-builders-bounty.git

# 2. Install
cd claude-builders-bounty/skills/security-hook
./install.sh
```

## How it works

The hook intercepts bash commands before Claude executes them and checks for dangerous patterns:

| Pattern | Blocked |
|---------|---------|
| `rm -rf` | ✅ |
| `DROP TABLE` | ✅ |
| `TRUNCATE` | ✅ |
| `DELETE FROM` (no WHERE) | ✅ |
| `git push --force` | ✅ |
| `git push -f` | ✅ |

## Log Format

```bash
# View blocked attempts
cat ~/.claude/hooks/blocked.log
```

Output:
```
2024-01-15T10:30:00Z | rm -rf / | rm -rf | /home/user/project
2024-01-15T10:31:00Z | DROP TABLE users; | DROP TABLE | /home/user/project
```

## Installation Details

| File | Purpose |
|------|---------|
| `pre-tool-use.sh` | Hook script |
| `install.sh` | Installation script |
| `README.md` | This file |

## Acceptance Criteria Met

- ✅ Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- ✅ Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- ✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log`
- ✅ Displays clear message explaining why command was blocked
- ✅ Does not interfere with normal bash commands
- ✅ README with installation in 2 commands