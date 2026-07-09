# Destructive Bash Command Hook

Claude Code `PreToolUse` hook for issue #3. It denies Bash tool calls that look like destructive file, Git, or SQL operations, then logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

```bash
bash hooks/block-destructive-bash/install.sh
```

The installer copies `block_destructive_bash.py` into `~/.claude/hooks/` and registers it under the `PreToolUse` Bash matcher in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`, including common flag order variants such as `rm -fr`, `rm -r -f`, and `sudo rm -rf`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- SQL containing `DELETE FROM` without a `WHERE` clause

Normal Bash commands exit silently with no hook decision, so Claude Code continues through its normal permission flow.

## Log Format

Each denied command appends one JSON line to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-07-09T00:00:00+00:00","attempted_command":"rm -rf build","project_path":"/repo","blocked_pattern":"rm -rf","reason":"Recursive forced removal can delete project or system files."}
```

## Test

```bash
python3 -m unittest tests/test_block_destructive_bash.py
```