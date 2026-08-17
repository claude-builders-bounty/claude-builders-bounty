# Block Destructive Commands Hook (Claude Code) 🛡️

> Pre-tool-use security hook for Claude Code that intercepts and blocks dangerous commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unconstrained `DELETE FROM`) before execution.

---

## Quickstart in 2 Commands

```bash
# 1. Create Claude Code hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the pre-tool-use hook
cp hooks/block-destructive-commands/pre_tool_use.py ~/.claude/hooks/pre-tool-use.py
```

---

## Blocked Patterns & Security Rules

| Pattern | Examples Blocked | Rationale |
|---|---|---|
| `rm -rf` | `rm -rf /dir`, `rm -r -f ./build`, `rm --recursive --force` | Prevents accidental unrecoverable file deletion. |
| `DROP TABLE / DATABASE` | `DROP TABLE users;`, `DROP DATABASE prod;` | Prevents accidental schema destruction. |
| `git push --force` | `git push -f`, `git push --force origin main` | Prevents overwriting remote repository commit history. |
| `TRUNCATE` | `TRUNCATE TABLE logs;`, `truncate sessions` | Prevents complete table data wiping. |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;`, `DELETE FROM orders` | Prevents full table row deletion without a filter clause. |

---

## Safe Commands are NOT Blocked
Normal non-destructive development commands continue to execute smoothly:
- `rm file.txt` (single file removal)
- `git push origin main` (normal branch push)
- `DELETE FROM users WHERE id = 42;` (targeted deletion with WHERE clause)
- `npm test`, `pnpm build`, `git status`, etc.

---

## Audit Logging

Every blocked execution attempt is automatically logged to:
`~/.claude/hooks/blocked.log`

```text
[2026-08-16T22:11:40] BLOCKED: "rm -rf ./dist" | REASON: Recursive force removal ('rm -rf') is forbidden to prevent accidental data loss. | PATH: /home/user/project
```

---

## Running Tests

```bash
python hooks/block-destructive-commands/tests/test_hook.py
```
