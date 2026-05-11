# Block Destructive Bash Commands

Claude Code `PreToolUse` hook for bounty #3. It blocks high-risk Bash commands before they run, logs the blocked attempt, and returns a clear denial reason to Claude using the current `hookSpecificOutput.permissionDecision` hook format.

## Install

```bash
python3 hooks/block-destructive-bash/install.py
```

That single command copies the hook to `~/.claude/hooks/block_destructive_bash.py` and registers it in `~/.claude/settings.json` with a `PreToolUse` matcher for `Bash`.

## What Gets Blocked

- `rm -rf`, `rm -fr`, and equivalent recursive-force `rm` flags.
- `git push --force`, `git push --force=...`, and `git push -f`.
- `DROP TABLE`.
- `TRUNCATE` and `TRUNCATE TABLE`.
- `DELETE FROM` statements that do not include a `WHERE` clause.

Normal Bash commands are left alone: the hook exits successfully with no stdout, so Claude Code continues without extra output. `git push --force-with-lease` is intentionally allowed because it checks the remote ref before rewriting history.

## Log Format

Every blocked command is appended to `~/.claude/hooks/blocked.log` as JSON Lines:

```json
{"timestamp":"2026-03-27T00:55:40.000000Z","attempted_command":"rm -rf /tmp/demo","project_path":"/path/to/project","reason":"Blocked recursive force delete (`rm -rf` / `rm -fr`) to prevent irreversible data loss."}
```

For tests or custom deployments, set `CLAUDE_BLOCKED_BASH_LOG` to override the log path.

## Test

```bash
python3 -m unittest discover hooks/block-destructive-bash/tests -v
```
