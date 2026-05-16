# claude-security-hook 🛡️

> **Claude Code PreToolUse hook** — Blocks destructive bash commands before they execute.

![bounty](https://img.shields.io/badge/bounty-%24100-brightgreen)
![opire](https://img.shields.io/badge/opire-try-blue)

---

## 🚀 Install in 2 Commands

```bash
mkdir -p ~/.claude/hooks/pre_tool_use
curl -sfL https://raw.githubusercontent.com/claude-builders-bounty/claude-security-hook/main/guard.py \
  -o ~/.claude/hooks/pre_tool_use/guard.py
```

Or copy directly:

```bash
mkdir -p ~/.claude/hooks/pre_tool_use
cp guard.py ~/.claude/hooks/pre_tool_use/
```

That's it — Claude Code automatically discovers hooks in `~/.claude/hooks/`.

---

## 🔒 What It Blocks

| Category | Patterns Blocked |
|----------|-----------------|
| **File Destruction** | `rm -rf`, `rm /`, forceful removal |
| **Git Destructive** | `git push --force`, `git reset --hard`, `git branch -D` |
| **Database** | `DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` (no WHERE), `ALTER TABLE DROP` |
| **System Danger** | `mkfs`, `dd if=`, `format`, `chmod 0`, `chown -R` |
| **Remote Code Execution** | `curl | bash`, `wget | bash` |

## ✅ What It Allows

Safe operations pass through normally:

- `rm -rf node_modules dist build .next __pycache__`
- `git reset --hard HEAD`
- `git push --force-with-lease`
- Normal `rm file.txt`, `mkdir`, `cp`, `mv`

---

## 📋 Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-16T17:00:00+00:00] BLOCKED | Destructive file removal (rm -rf) | cmd: rm -rf /var/log/ | project: /home/user/project
```

---

## 🧪 Test

```bash
# Test — should be blocked
python3 guard.py <<< '{"args":{"command":"rm -rf /important"}}'

# Test — should be allowed (safe path)
python3 guard.py <<< '{"args":{"command":"rm -rf node_modules"}}'

# Test — should be allowed (normal command)
python3 guard.py <<< '{"args":{"command":"ls -la"}}'
```

---

## 🔧 Customization

To add custom patterns, edit `guard.py` and modify the `DANGEROUS_PATTERNS` or `ALLOWLIST` lists.

---

## 🏆 Bounty

This project is a submission for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — **$100 reward**.

**Acceptance Criteria:**
- [x] Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs to `~/.claude/hooks/blocked.log` with timestamp, command, project path
- [x] Clear message explaining why command was blocked
- [x] Does not interfere with normal bash commands
- [x] README with 2-command install

---

## 📄 License

MIT — built for the Claude Builder community.
