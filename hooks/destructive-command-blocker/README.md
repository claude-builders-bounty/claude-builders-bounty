# Pre-Tool-Use Hook: Destructive Command Blocker

A lightweight, reliable security hook for Claude Code / autonomous coding agents that intercepts and halts destructive bash and SQL commands before execution.

## 💰 Solves Bounty: $100 — [Opire Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

---

## 🛡️ Blocked Patterns
This hook intercepts and blocks:
1. `rm -rf` (recursive force deletion of directories)
2. `DROP TABLE` (destructive SQL database schema deletion)
3. `git push --force` or `git push -f` (destructive history rewrites)
4. `TRUNCATE` / `TRUNCATE TABLE` (database table wipes)
5. `DELETE FROM ...` without a `WHERE` clause (unconstrained bulk table deletion)

---

## ⚡ Setup in 3 Steps

### Step 1: Copy Hook into Claude Hooks Directory
```bash
mkdir -p ~/.claude/hooks
cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

### Step 2: Register in Claude Settings
Add to your `~/.claude/settings.json`:
```json
{
  "hooks": {
    "preToolUse": "python3 ~/.claude/hooks/pre-tool-use.py"
  }
}
```

### Step 3: Verify Protection
Run the test command:
```bash
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/data"}}' | python3 block_destructive_commands.py
```

Output:
```text
🚫 [BLOCKED BY SECURITY HOOK]: Dangerous recursive force delete ('rm -rf')
Attempted Command: rm -rf /tmp/data
Logged to: ~/.claude/hooks/blocked.log
Action Refused: Destructive command rejected to protect repository and database integrity.
```

---

## 📋 Audit Log
Every blocked command is recorded with ISO timestamp, working directory, and the exact blocked command in `~/.claude/hooks/blocked.log`:
```text
[2026-11-23T12:08:00Z] REJECTED: Dangerous recursive force delete ('rm -rf') | CWD: /project | CMD: rm -rf /tmp/data
```
