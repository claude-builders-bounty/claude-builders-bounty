# HookGuard — pre-tool-use hook that blocks destructive bash commands

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) `pre-tool-use`
hook that intercepts dangerous bash commands **before** they run.

Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`,
`DELETE FROM` without a `WHERE`/`LIMIT` clause — plus `mkfs`, raw `dd` to
block devices, and root `chmod 777 /` / `chown -R ... /`.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/
cat >> ~/.claude/settings.json <<'EOF'
{ "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" } ] } ] } }
EOF
```

> If `~/.claude/settings.json` already exists, merge the `hooks` key instead.

## How it works

Claude Code invokes the hook with a JSON payload on stdin
(`{"tool_name": "Bash", "tool_input": {"command": "..."}}`). The hook replies
with a JSON `permissionDecision`:

- `block` — a destructive pattern matched. The reason is returned to Claude
  and every blocked attempt is appended to `~/.claude/hooks/blocked.log`:
  `[timestamp] project=<cwd> command='...' reason=...`
- `allow` — normal commands pass through untouched.

## Design notes

- **No false positives on inert text.** Commands that only read/output text
  (`echo`, `grep`, `cat`, `head`, …) are scanned with quoted content removed,
  so `echo 'rm -rf /'` or `grep -r "DROP TABLE" .` pass through. Real
  executions (`mysql -e "DELETE FROM users"`) are scanned raw and blocked.
- **`rm` flag handling.** Recursive+force is detected whether flags are
  combined (`rm -rf`), split (`rm -r -f`), or long form
  (`rm --recursive --force`). Plain `rm -f file` or `rm -r dir` are allowed.
- **Fails open.** If the hook itself errors (bad JSON, missing fields), the
  tool call is allowed — the hook never breaks Claude on its own bugs.

## Test

```bash
python3 test_hook.py   # 26 cases: destructive patterns, quoting, pipelines
```
