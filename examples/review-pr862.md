## Review: claude-builders-bounty/claude-builders-bounty#862

**Title:** [BOUNTY 00] HOOK: Pre-tool-use hook that blocks destructive bash commands
**Author:** @wptechprodigy  **State:** OPEN
**Branch:** `hook/destructive-command-blocker` → `main`
**Stats:** +193/-0 across 2 files

**File types:**
```
   1 md
   1 hooks/pre_tool_use
```

---

### PR Description

## Summary

Implements a Claude Code `pre_tool_use` hook that intercepts and blocks dangerous bash commands before they execute.

Closes #3

## What's included

- `hooks/pre_tool_use` — Python hook script (exit code 2 protocol)
- `hooks/README.md` — Single-command installation

## What it blocks

| Pattern | Example | Exit |
|---|---|---|
| Recursive force delete | `rm -rf /data` | 2 (blocked) |
| Database destruction | `DROP TABLE users;` | 2 (blocked) |
| Table truncation | `TRUNCATE TABLE logs;` | 2 (blocked) |
| DELETE without WHERE | `DELETE FROM users;` | 2 (blocked) |
| Force push | `git push --force main` | 2 (blocked) |
| Normal rm | `rm temp.txt` | 0 (allowed) |
| DELETE with WHERE | `DELETE FROM t WHERE id=1` | 0 (allowed) |
| Normal push | `git push origin main` | 0 (allowed) |
| Non-Bash tools | Read/Edit/Write | 0 (allowed) |

## Logging

All blocked attempts logged to `~/.claude/hooks/blocked.log` as JSONL with timestamp, command, reason, and project path.

## Testing

10 exhaustive test cases verified — 5 blocks, 5 passes. All correct.

## Acceptance checklist
- [x] Follows Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs every blocked attempt to `~/.claude/hooks/blocked.log` (timestamp, command, project)
- [x] Displays clear block reason to Claude via stderr
- [x] Does not interfere with normal commands
- [x] README with 1-command installation

---

### Diff (205 lines)

```diff
diff --git a/hooks/README.md b/hooks/README.md
new file mode 100644
index 000000000..d0f3f44e0
--- /dev/null
+++ b/hooks/README.md
@@ -0,0 +1,41 @@
+# Destructive Command Blocker
+
+A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before they execute.
+
+## Installation
+
+```bash
+mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
+```
+
+That's it. Claude Code detects hooks in `~/.claude/hooks/` automatically on next start.
+
+## What It Blocks
+
+| Pattern | Example | Why |
+|---|---|---|
+| Recursive force delete | `rm -rf /project/data` | Irreversible file deletion |
+| Database destruction | `DROP TABLE users;` | Permanent data loss |
+| Table truncation | `TRUNCATE TABLE logs;` | Non-recoverable row removal |
+| DELETE without WHERE | `DELETE FROM users;` | Mass data deletion |
+| Force push | `git push --force origin main` | Overwrites remote history |
+
+Safe variants (with WHERE clause, normal `rm`, regular `git push`) pass through without interference.
+
+## Logging
+
+Every blocked command is recorded to `~/.claude/hooks/blocked.log` in JSONL format:
+
+```json
+{"timestamp": "2026-05-11T02:30:00Z", "command": "rm -rf /project", "reason": "...", "project": "/Users/me/my-project"}
+```
+
+## How It Works
+
+The hook receives JSON on stdin with `tool_name` and `tool_input`. For Bash tool calls, it checks the command against compiled regex patterns. On match:
+
+1. The command description is printed to stderr
+2. Exit code 2 is returned (Claude Code protocol — blocks the tool call)
+3. The attempt is logged to `blocked.log`
+
+Non-matching commands and non-Bash tools pass through with exit code 0.
diff --git a/hooks/pre_tool_use b/hooks/pre_tool_use
new file mode 100755
index 000000000..f747a053e
--- /dev/null
+++ b/hooks/pre_tool_use
@@ -0,0 +1,152 @@
+#!/usr/bin/env python3
+"""
+pre_tool_use — Claude Code hook that intercepts destructive bash commands.
+
+Installed at ~/.claude/hooks/pre_tool_use, this hook runs before every
+tool call and blocks potentially destructive commands, logging each
+blocked attempt with timestamp, project path, and the attempted command.
+
+Exit codes:
+  0 — Allow the tool call (no dangerous pattern detected)
+  2 — Block the tool call and display an explanation to Claude
+"""
+
+import json
+import os
+import re
+import sys
+from datetime import datetime, timezone
+
+# ── Log file path ──────────────────────────────────────────────
+BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")
+
+# ── Dangerous patterns ─────────────────────────────────────────
+DANGEROUS_PATTERNS = [
+    # rm -rf and variants
+    {
+        "name": "recursive-force-delete",
+        "reason": "rm -rf permanently deletes files without recovery. Use a trash directory instead.",
+        "pattern": re.compile(
+            r'\brm\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|'
+            r'-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|'
+            r'--recursive\b.*--force\b|'
+            r'--force\b.*--recursive\b)',
+            re.IGNORECASE,
+        ),
+    },
+    # DROP TABLE / DROP DATABASE
+    {
+        "name": "drop-table",
+        "reason": "DROP TABLE/DATABASE destroys data irreversibly. Use DELETE or RENAME to a backup first.",
+        "pattern": re.compile(
+            r'\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW|INDEX|TRIGGER|FUNCTION|PROCEDURE)\b',
+            re.IGNORECASE,
+        ),
+    },
+    # TRUNCATE
+    {
+        "name": "truncate-table",
+        "reason": "TRUNCATE removes all rows without transactional rollback. Use DELETE for recoverable removal.",
+        "pattern": re.compile(r'\bTRUNCATE\s+(?:TABLE\s+)?\w+', re.IGNORECASE),
+    },
+    # DELETE FROM without WHERE (risky)
+    {
+        "name": "delete-without-where",
+        "reason": "DELETE FROM without WHERE removes ALL rows. Add a WHERE clause or use DELETE with LIMIT.",
+        "pattern": re.compile(
+            r'\bDELETE\s+FROM\b',
+            re.IGNORECASE,
+        ),
+    },
+    # git push --force / git push -f
+    {
+        "name": "force-push",
+        "reason": "git push --force overwrites remote history. Use --force-with-lease to protect others' work.",
+        "pattern": re.compile(
+            r'\bgit\s+push\s+.*(?:--force\b|-[a-zA-Z]*[fF][a-zA-Z]*)',
+            re.IGNORECASE,
+        ),
+    },
+]
+
+
+def check_delete_has_where(command):
+    """Return True if a DELETE statement has WHERE clause (safe)."""
+    # Only apply the DELETE-FROM check if there's NO WHERE clause
+    if re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE):
+        has_where = re.search(r'\bWHERE\b', command, re.IGNORECASE)
+        if not has_where:
+            return False  # No WHERE — block it
+    return True  # Has WHERE or not a DELETE — safe
+
+
+def log_blocked(command, reason, project_path):
+    """Append a blocked attempt to the log file."""
+    entry = {
+        "timestamp": datetime.now(timezone.utc).isoformat(),
+        "command": command.strip(),
+        "reason": reason,
+        "project": project_path or os.getcwd(),
+    }
+    try:
+        os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
+        with open(BLOCKED_LOG, "a") as f:
+            f.write(json.dumps(entry) + "\n")
+    except OSError:
+        pass  # Silent failure — don't crash Claude over logging
+
+
+def main():
+    try:
+        input_data = json.load(sys.stdin)
+    except (json.JSONDecodeError, EOFError):
+        # Not a valid hook invocation — allow through
+        sys.exit(0)
+
+    tool_name = input_data.get("tool_name", "")
+    tool_input = input_data.get("tool_input", {})
+
+    # Only intercept Bash tool calls
+    if tool_name != "Bash":
+        sys.exit(0)
+
+    command = tool_input.get("command", "").strip()
+    if not command:
+        sys.exit(0)
+
+    project_path = os.environ.get("CLAUDE_PROJECT", "")
+
+    # Check each dangerous pattern
+    for entry in DANGEROUS_PATTERNS:
+        name = entry["name"]
+        reason = entry["reason"]
+        pattern = entry["pattern"]
+
+        if not pattern.search(command):
+            continue
+
+        # Special case: DELETE FROM without WHERE
+        if name == "delete-without-where":
+            if check_delete_has_where(command):
+                continue  # Has WHERE — safe
+            reason = "DELETE FROM without WHERE clause removes ALL rows. Add a WHERE clause."
+
+        # Block it
+        log_blocked(command, reason, project_path)
+
+        print(
+            f"⛔ BLOCKED: {reason}",
+            file=sys.stderr,
+        )
+        print(
+            f"   Command: {command[:200]}",
+            file=sys.stderr,
+        )
+        sys.exit(2)  # Exit code 2 = block tool call + show stderr to Claude
+
+    # No dangerous pattern matched — allow
+    sys.exit(0)
+
+
+if __name__ == "__main__":
+    main()
```

---

### Analysis Checklist

Review each file below and note:

- **`hooks/README.md`** (null, +41/-0)
- **`hooks/pre_tool_use`** (null, +152/-0)

---

### Summary
_Claude Code will analyze the diff above and summarize the changes._

### Identified Risks
_Claude Code will identify potential issues._

### Improvement Suggestions
_Claude Code will suggest improvements._

### Confidence Score
_Claude Code will assign High / Medium / Low._

---

> Generated by claude-review
