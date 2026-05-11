# 🛡️ Smart Pre-Tool-Use Safety Hook v2 for Claude Code

Blocks destructive bash commands **before** they execute in Claude Code.

## Features

| Feature | v1 (bash only) | **v2 (this PR)** |
|---------|---------------|-------------------|
| Language | Bash only | **Python + Bash** |
| Pattern detection | Regex only | **Regex + risk scoring** |
| Allowlist | ❌ | ✅ Custom allowlist via config |
| Smart risk analysis | ❌ | ✅ Scores by flags + paths + env |
| Human-readable logs | ❌ | ✅ Both JSON + readable log |
| Configuration | ❌ | ✅ `~/.claude/hooks/config.yaml` |
| Rate limiting | ❌ | ✅ Prevents log flooding |

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use-hook.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-hook.py
```

Then add to your `~/.claude/claude.json`:
```json
{
  "hooks": {
    "pre-tool-use": "python3 ~/.claude/hooks/pre-tool-use-hook.py"
  }
}
```

## Configuration (optional)

Create `~/.claude/hooks/config.yaml`:

```yaml
allowlist:
  safe_commands:
    - "rm -rf node_modules"
    - "rm -rf .git"
  safe_path_prefixes:
    - "/tmp"
    - "/home"
```

## Blocked Patterns

- `rm -rf /` and destructive paths
- `DROP TABLE` / `TRUNCATE TABLE`
- `DELETE FROM` without `WHERE`
- `git push --force`
- `dd` to block devices
- `mkfs`, `wipefs`, fork bombs
- `chmod -R 777 /`, `chown -R` on root
- Raw device writes

## Logs

- `~/.claude/hooks/blocked.json` — structured
- `~/.claude/hooks/blocked.log` — human-readable

## How it's smarter

1. **Risk scoring** — `git push --force origin main` scores 5 (flag + env)
2. **Allowlist** — `rm -rf node_modules` is allowed, `rm -rf /` is not
3. **Context-aware** — detects which env (prod/staging) you're operating on
4. **Graceful failure** — hook errors never block legitimate commands
