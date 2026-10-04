# Block destructive bash commands (Claude Code PreToolUse hook)

Pre-tool hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that blocks dangerous `Bash` commands before they run. Closes #3.

**Blocked patterns**

- `rm -rf` (`rm` with both `-r` and `-f`)
- `DROP TABLE`
- `git push --force` (including `-f` and `--force-with-lease`)
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as
`{ISO8601 UTC}\tproject={cwd}\tcommand={full command}`.
Claude receives a clear deny reason via stderr + hook JSON (`permissionDecision: deny`, exit 2).
Safe commands exit 0 and don't interfere with normal flow.

## Install (1 command)

```bash
bash hooks/block-destructive-bash/install.sh
```

That copies `block_destructive.py` to `~/.claude/hooks/`, makes it executable, and merges the `PreToolUse` → `Bash` entry into `~/.claude/settings.json` (idempotent).

## Test

```bash
bash hooks/block-destructive-bash/test_hook.sh
```

Expected: 6 blocked cases (exit 2) + 7 allowed cases (exit 0), log line count + format checks pass.
Verified locally — see PR description for full output.

## Manual `settings.json` snippet

If you register by hand, add under `hooks.PreToolUse`:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/block_destructive.py"
    }
  ]
}
```
