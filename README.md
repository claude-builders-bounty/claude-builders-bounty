# Dangerous Command Guard

A Claude Code pre-tool-use hook that blocks destructive bash commands before they execute.

## Install in 3 steps

**Step 1 — Copy the hook**

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/dangerous_command_guard.py ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/dangerous_command_guard.py
```

**Step 2 — Register it in Claude Code settings**

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/dangerous_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

**Step 3 — Verify**

```bash
python3 ~/.claude/hooks/pre-tool-use/dangerous_command_guard.py <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}
EOF
# → {"decision": "block", "reason": "BLOCKED by dangerous_command_guard: ..."}
```

---

## What it blocks

| Category      | Examples |
|---------------|----------|
| Filesystem    | `rm -rf`, `rm -fr`, `find … -delete`, `dd if=/dev/zero`, `mkfs`, `shred` |
| SQL           | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| Git           | `git push --force`, `git push -f`, `git reset --hard HEAD~`, `git clean -fd` |
| Kubernetes    | `kubectl delete namespace`, `kubectl delete all --all`, `--all-namespaces` |
| System        | `kill -1`, fork bombs, writing to raw block devices (`/dev/sda`) |

Safe alternatives are **not** blocked — e.g. `git push --force-with-lease`, `DELETE FROM … WHERE id = 1`.

---

## Example blocked output

```
────────────────────────────────────────────────────────────────────────
✗  BLOCKED — severity: CRITICAL
────────────────────────────────────────────────────────────────────────
  Reason  : rm with recursive+force flags (rm -rf …)
  Command : rm -rf /
  Project : /home/user/my-project

  To allow once: ALLOW_DANGEROUS=1 <re-run>
  Audit log    : /home/user/.claude/hooks/blocked.log
────────────────────────────────────────────────────────────────────────
```

Claude receives: `{"decision": "block", "reason": "BLOCKED by dangerous_command_guard: rm with recursive+force flags (rm -rf …). This command was blocked because it is potentially destructive and irreversible. If you are certain this is safe, ask the user to re-run with ALLOW_DANGEROUS=1 (audit-logged)."}`

---

## Environment variables

| Variable           | Effect |
|--------------------|--------|
| `ALLOW_DANGEROUS=1` | Override the block for one command (still audit-logged as `OVERRIDE_ALLOWED`) |
| `HOOK_DRY_RUN=1`   | Explain what would be blocked without actually blocking (returns `allow`) |

---

## Audit log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-03-28T12:00:00Z] BLOCKED | project='/home/user/proj' | reason='rm with recursive+force flags (rm -rf …)' | cmd='rm -rf /'
[2026-03-28T12:05:00Z] OVERRIDE_ALLOWED | project='/home/user/proj' | reason='git push --force / -f …' | cmd='git push -f origin main'
```

---

## Bash alternative

A pure-bash version is included at `hooks/pre-tool-use/dangerous_command_guard.sh` for environments without Python 3. Replace the `command` in `settings.json` with:

```json
"command": "bash ~/.claude/hooks/pre-tool-use/dangerous_command_guard.sh"
```

Requires `jq` (preferred) or `python3` for JSON parsing.

---

## Running the tests

```bash
python3 -m pytest tests/test_hook.py -v
# 54 tests: filesystem, SQL, git, kubernetes, end-to-end
```

---

## Pattern details

All detection uses compiled regular expressions (not simple string matching) to resist common bypass attempts:

- Flag order variants: `-rf` and `-fr` both caught
- Case-insensitive SQL: `drop table` = `DROP TABLE`
- Negative lookahead: `--force-with-lease` is allowed, `--force` is blocked
- `DELETE FROM` without `WHERE` is blocked; with a real `WHERE` clause it is allowed
- `WHERE 1=1` (deletes everything) is caught as a separate critical pattern
