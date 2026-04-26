# How-To Guide: Block Destructive Bash Commands in Claude Code

A step-by-step walkthrough for installing, customizing, and monitoring the safety hook.

---

## Quick Install (2 minutes)

### Step 1: Copy the hook

```bash
mkdir -p ~/.claude/hooks
cp block-destructive.py ~/.claude/hooks/block-destructive.py
```

### Step 2: Configure Claude Code

Edit `~/.claude/settings.json` (create it if it doesn't exist):

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

### Step 3: Verify it works

Ask Claude Code to run a dangerous command. It should be blocked:

```
You: "run rm -rf /tmp/test"
Claude: BLOCKED: rm -rf detected.
Reason: Recursive force delete — can wipe entire directories
```

---

## How It Works

```
User asks Claude to run a command
        ↓
Claude calls Bash tool
        ↓
Hook receives: {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
        ↓
Hook checks command against 13 regex patterns
        ↓
    ┌─── Match found?
    │
    ├── YES → Log to blocked.log → Exit code 2 (BLOCKED) → Claude sees error message
    │
    └── NO  → Exit code 0 (ALLOWED) → Command runs normally
```

---

## Customizing Patterns

### Add a new pattern

Open `block-destructive.py` and add to the `DANGEROUS_PATTERNS` list:

```python
{
    "pattern": r"\bsudo\s+rm\b",
    "name": "sudo rm",
    "description": "Running rm with sudo — extra dangerous",
    "severity": "critical",
},
```

### Remove a pattern

Comment out or delete the pattern from the list. For example, if you want to allow `git push --force`:

```python
# {
#     "pattern": r"\bgit\s+push\s+.*--force\b",
#     "name": "git push --force",
#     ...
# },
```

### Change severity

Edit the `"severity"` field:
- `"critical"` — data loss, irreversible
- `"high"` — dangerous but recoverable
- `"medium"` — risky but sometimes needed
- `"low"` — just a warning

---

## Monitoring Blocked Commands

### View the log

```bash
cat ~/.claude/hooks/blocked.log
```

Each line is JSON:

```json
{
  "timestamp": "2026-04-15T14:30:00.123456",
  "command": "rm -rf /important-data",
  "blocked_pattern": "rm -rf",
  "description": "Recursive force delete — can wipe entire directories",
  "severity": "critical",
  "project_path": "/home/user/my-project"
}
```

### Quick stats

```bash
# Count total blocks
wc -l ~/.claude/hooks/blocked.log

# Most common blocked patterns
cat ~/.claude/hooks/blocked.log | python -c "
import sys, json
from collections import Counter
patterns = Counter()
for line in sys.stdin:
    d = json.loads(line)
    patterns[d['blocked_pattern']] += 1
for name, count in patterns.most_common():
    print(f'  {count:3d}x  {name}')
"

# Recent blocks
tail -5 ~/.claude/hooks/blocked.log | python -m json.tool
```

### Clear the log

```bash
> ~/.claude/hooks/blocked.log
```

---

## Real-World Examples

### Example 1: Accidental recursive delete

Claude tries to clean up a temp directory:

```
Command: rm -rf ./build/output/../../../
Result:  BLOCKED — rm -rf detected (path traversal could delete parent dirs)
```

### Example 2: SQL without WHERE

Claude tries to update a database:

```
Command: DELETE FROM sessions
Result:  BLOCKED — DELETE FROM without WHERE (would delete ALL sessions)
Better:  DELETE FROM sessions WHERE expires_at < NOW()
```

### Example 3: Force push to main

Claude tries to fix a commit:

```
Command: git push --force origin main
Result:  BLOCKED — git push --force (would overwrite remote history)
Better:  git push origin main (normal push, or git push --force-with-lease for safer override)
```

### Example 4: Safe commands pass through

```
Command: rm ./temp.log          → ALLOWED (no -rf flag)
Command: git push origin main   → ALLOWED (no --force)
Command: DELETE FROM users WHERE id = 5  → ALLOWED (has WHERE clause)
Command: chmod 755 script.sh    → ALLOWED (not 777)
```

---

## Troubleshooting

**"Hook not running"**
- Check `~/.claude/settings.json` syntax (valid JSON?)
- Verify Python is in PATH: `which python` or `which python3`
- Check the hook file exists: `ls ~/.claude/hooks/block-destructive.py`

**"Safe commands being blocked"**
- Check if the command accidentally matches a pattern (e.g., a variable named `$rm_rf`)
- Open an issue or customize the regex

**"Hook errors crashing Claude"**
- The hook is designed to fail-open (exit 0 on errors)
- If it's still crashing, check Python version (needs 3.8+)

**"Log file growing too large"**
- The log only grows when commands are blocked (not on every command)
- Rotate or clear periodically: `> ~/.claude/hooks/blocked.log`

---

## For Teams

### Shared configuration

Commit the hook to your repo so the whole team uses it:

```bash
# In your project
mkdir -p .claude/hooks
cp ~/.claude/hooks/block-destructive.py .claude/hooks/
```

Add to your project's `CLAUDE.md`:

```markdown
## Safety
This project uses a pre-tool-use hook to block destructive commands.
See `.claude/hooks/block-destructive.py` for the pattern list.
```

### CI/CD integration

You can also use the pattern list as a pre-commit check:

```yaml
# .github/workflows/safety.yml
- name: Check for destructive commands in scripts
  run: |
    python block-destructive.py < <(echo '{"tool_name":"Bash","tool_input":{"command":"'"$(cat deploy.sh)"'"}}')
```
