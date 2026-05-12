# Claude destructive bash guard

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before they run.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

- timestamp
- attempted command
- project path
- block reason

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/
cat hooks/settings.example.json >> ~/.claude/settings.json
```

## Usage

Once installed, Claude Code calls the hook before Bash tool use. Safe commands continue normally. Dangerous commands return a clear block message to Claude.

Example block response:

```json
{
  "decision": "block",
  "reason": "Blocked destructive bash command: rm -rf removes files recursively and forcefully. Review the command and use a safer, explicit alternative."
}
```

## Test

```bash
python -m unittest tests/test_block_destructive_bash.py
```

If `pytest` is unavailable, the hook itself has no runtime dependency beyond Python 3.10+.
