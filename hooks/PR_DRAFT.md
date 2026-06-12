# PR Draft: Add Destructive Bash Command Blocker Hook

Closes #3.

## Summary

- Adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` as JSON Lines with timestamp, command, project path, and reason.
- Documents a one-command install path and includes regression tests for blocked and allowed commands.

## Acceptance Criteria

- Hook path/format: `hooks/block_destructive_bash.py`, installable into `~/.claude/hooks/`
- Blocks:
  - `rm -rf`, including separated flags like `rm -r -f` and `sudo rm -rf`
  - `DROP TABLE`
  - `git push --force` and `git push --force-with-lease`
  - `TRUNCATE`
  - `DELETE FROM` without a `WHERE` clause
- Logs blocked attempts to `~/.claude/hooks/blocked.log`
- Prints a clear block message to stderr for Claude
- Allows normal bash commands without logging
- README: `hooks/README.md`

## Verification

```bash
python3 tests/test_block_destructive_bash.py
python3 hooks/block_destructive_bash.py <<'JSON'
{"tool_name":"Bash","tool_input":{"command":"rm -r -f /tmp/demo"},"cwd":"/tmp/project"}
JSON
```

Expected:

```text
Blocked destructive bash command: recursive force delete...
```

## Local Submit Steps

```bash
git checkout bounty-3-destructive-bash-hook
git add .gitignore README.md hooks/README.md hooks/block_destructive_bash.py tests/test_block_destructive_bash.py hooks/PR_DRAFT.md
git commit -m "Add destructive bash command blocker hook"
git push <your-fork> bounty-3-destructive-bash-hook
```

## Claim

After opening the PR, comment on issue #3:

```text
/opire try

Submitted PR: <PR URL>

This completes the destructive Bash command blocker hook bounty with Claude Code hook installation docs, blocked.log auditing, clear denial output, and regression tests for blocked and allowed commands.
```
