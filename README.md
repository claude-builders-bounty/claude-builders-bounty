# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

---

## Pre-Tool-Use Hook: Block Destructive Bash Commands

This repository includes a production-ready `pre-tool-use` hook for **Claude Code** that intercepts dangerous bash commands before execution.

### Features
- 🛡️ **Blocks Destructive Patterns**:
  - `rm -rf` (recursive file deletion)
  - `DROP TABLE` (SQL schema destruction)
  - `git push --force` / `-f` (remote history overwrite)
  - `TRUNCATE` (table truncation)
  - `DELETE FROM` without a `WHERE` clause (allows safe `DELETE FROM ... WHERE ...`)
- 🛑 **Claude Code Guardrail Native**: Returns exit code `2` with descriptive feedback on `stderr` for Claude.
- 📝 **Audit Logging**: Appends all blocked attempts to `~/.claude/hooks/blocked.log` (timestamp, command, cwd).
- ⚡ **Zero Friction**: Permits safe commands (`git status`, `ls`, `npm test`, etc.) instantly with exit code `0`.

### Installation (2 commands or fewer)

```bash
# 1. Install hook to ~/.claude/hooks/
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py

# 2. Register hook in ~/.claude/settings.json
python3 -c 'import json, pathlib; p = pathlib.Path.home() / ".claude" / "settings.json"; p.parent.mkdir(parents=True, exist_ok=True); d = json.loads(p.read_text()) if p.exists() else {}; d.setdefault("hooks", {}).setdefault("PreToolUse", []).append({"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 {pathlib.Path.home()}/.claude/hooks/block_destructive.py"}]}); p.write_text(json.dumps(d, indent=2)); print("✅ Claude Code Hook Configured!")'
```

### Running Tests

```bash
python3 tests/test_block_destructive.py
```
